"""Launch only this runner's Blender child, once, with a 60s native budget."""
import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_common import file_record, load_inputs, verify_inputs, write_new


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def record_exit_observation(record, exit_code, observed_at, deadline, start, phase):
    """Bind the first actual terminal observation to its deadline immediately.

    Later cleanup observations cannot replace a timely first terminal time.
    The actual exit code is retained even if the first observation was late.
    """
    if exit_code is not None:
        within_deadline = observed_at <= deadline
        if record.get('first_terminal_observed_monotonic') is None:
            record.update(native_exit_code=exit_code,
                          first_terminal_observed_monotonic=observed_at,
                          first_terminal_observed_elapsed_seconds=observed_at - start,
                          first_terminal_observation_phase=phase,
                          terminal_observed_within_native_deadline=within_deadline)
            if not within_deadline:
                record['timed_out'] = True
                record['deadline_failure_reason'] = 'FIRST_TERMINAL_OBSERVATION_AFTER_NATIVE_DEADLINE'
        else:
            assert record['native_exit_code'] == exit_code
    return exit_code


def native_exit_passes(record):
    return (record.get('native_exit_code') == 0 and not record['timed_out']
            and record.get('terminal_observed_within_native_deadline') is True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--window-note', required=True, help='Honest competing-work context; never an isolated benchmark claim')
    args = parser.parse_args()
    assert args.window_note.strip()
    cfg = load_inputs(args.inputs)
    budget = cfg['execution']
    assert budget == {'cpu_count': 2, 'native_budget_seconds': 60,
                      'term_grace_seconds': 1, 'kill_grace_seconds': 2}
    folder = Path(__file__).resolve().parent
    preparation = json.loads(args.preparation.read_text())
    assert preparation['status'] == 'PREPARED_NOT_EXECUTED_READY_FOR_INDEPENDENT_REVIEW'
    for name, expected in preparation['prepared_files'].items():
        assert Path(name).name == name
        actual = file_record(folder / name)
        assert {key: actual[key] for key in ('bytes', 'sha256')} == expected, ('preparation changed', name)
    assert args.inputs.resolve() == folder / 'inputs.json'
    before = verify_inputs(cfg)
    scripts = [folder / n for n in ('graph_common.py', 'inspect_native_graph.py',
                                   'run_graph_inspection.py', 'check_deadline_controls.py',
                                   'check_station_roles.py')]
    for script in scripts:
        compile(script.read_bytes(), str(script), 'exec')
    protection_paths = scripts + [args.inputs.resolve(), args.preparation.resolve()]
    prepared_before = {str(p): file_record(p) for p in protection_paths}
    assert not args.output.exists() and args.output.parent.is_dir()
    output = args.output.resolve()
    # Fresh outputs are siblings beneath this dedicated preparation folder.
    assert output.parent == folder, 'Output must be a new direct child of the dedicated package'
    output.mkdir()
    cpus = sorted(os.sched_getaffinity(0))[:2]
    assert len(cpus) == 2, 'Exactly two available CPUs required'
    command = ['taskset', '-c', ','.join(map(str, cpus)), cfg['inputs']['blender']['path'],
               '--background', '--factory-startup', '--disable-autoexec', '--threads', '2',
               '--python-exit-code', '1', '--python', str(folder / 'inspect_native_graph.py'), '--',
               '--inputs', str(args.inputs.resolve()), '--output', str(output / 'native')]
    record = {'status': 'NOT_LAUNCHED', 'command': command, 'window_note': args.window_note,
              'started_utc': utc(), 'native_budget_seconds': 60, 'cleanup_budget_seconds': 3,
              'cpu_affinity': cpus, 'inputs_before': before, 'preparation_before': prepared_before,
              'performance_claim': 'Operational elapsed time only; concurrent resource contention is not isolated',
              'native_exit_code': None, 'timed_out': False, 'termination_status': 'NOT_LAUNCHED',
              'all16_vehicle_gates': 'OPEN', 'model_saved': False, 'exported': False, 'rendered': False}
    write_new(output / 'launch.json', record)
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2',
               PYTHONDONTWRITEBYTECODE='1')
    proc = None
    start = time.monotonic()
    deadline = start + 60
    record.update(native_started_monotonic=start, native_deadline_monotonic=deadline)
    interrupted = False
    previous_handlers = {}
    def interrupt(signum, frame):
        raise InterruptedError('Runner received signal ' + str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT):
        previous_handlers[signum] = signal.signal(signum, interrupt)
    def poll_observed(phase):
        code = proc.poll()
        observed_at = time.monotonic()
        record_exit_observation(record, code, observed_at, deadline, start, phase)
        return code, observed_at
    def wait_observed(timeout, phase):
        code = proc.wait(timeout=timeout)
        observed_at = time.monotonic()
        return record_exit_observation(record, code, observed_at, deadline, start, phase)
    try:
        with (output / 'run.log').open('xb') as log, (output / 'heartbeat.jsonl').open('x') as heartbeat:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                    env=env, start_new_session=True)
            record.update(status='RUNNING', child_pid=proc.pid, owned_process_group=proc.pid)
            write_new(output / 'child-started.json', {'child_pid': proc.pid, 'started_utc': utc(),
                                                     'owned_process_group': proc.pid})
            while True:
                code, now = poll_observed('native')
                if code is not None:
                    break
                heartbeat.write(json.dumps({'utc': utc(), 'elapsed_seconds': now - start,
                                             'child_pid': proc.pid, 'child_exit_code': code}) + '\n')
                heartbeat.flush()
                if now >= deadline:
                    record['timed_out'] = True
                    record['deadline_failure_reason'] = 'NATIVE_DEADLINE_REACHED_WITHOUT_TERMINAL_OBSERVATION'
                    break
                try:
                    wait_observed(timeout=min(1, deadline - now), phase='native')
                    break
                except subprocess.TimeoutExpired:
                    pass
    except BaseException as exc:
        interrupted = True
        record['runner_error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        # This boundary is separate from cleanup and terminal-observation times.
        record['native_phase_ended_monotonic'] = time.monotonic()
        record['native_phase_elapsed_seconds'] = record['native_phase_ended_monotonic'] - start
        # Only the process group created above is eligible for cleanup.
        # Ignore repeat interruption during this bounded cleanup/report section.
        for signum in previous_handlers:
            signal.signal(signum, signal.SIG_IGN)
        record['cleanup_actions'] = []
        if proc is not None and poll_observed('cleanup')[0] is None:
            try:
                assert os.getpgid(proc.pid) == proc.pid
                os.killpg(proc.pid, signal.SIGTERM)
                record['cleanup_actions'].append('SIGTERM_OWNED_GROUP')
                try:
                    wait_observed(timeout=1, phase='cleanup')
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    record['cleanup_actions'].append('SIGKILL_OWNED_GROUP')
                    wait_observed(timeout=2, phase='cleanup')
            except BaseException as exc:
                record['cleanup_error'] = type(exc).__name__ + ': ' + str(exc)
        final_code = poll_observed('cleanup')[0] if proc is not None else None
        record['termination_status'] = ('NOT_LAUNCHED' if proc is None else 'CHILD_EXIT_CONFIRMED'
                                         if final_code is not None else 'TERMINATION_UNCONFIRMED')
        record['elapsed_seconds_through_cleanup'] = time.monotonic() - start
        record['peak_child_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        record['finished_utc'] = utc()
        try:
            record['inputs_after'] = {key: file_record(row['path']) for key, row in cfg['inputs'].items()}
            record['preparation_after'] = {str(p): file_record(p) for p in protection_paths}
            record['protected_inputs_unchanged'] = record['inputs_after'] == before and record['preparation_after'] == prepared_before
        except BaseException as exc:
            record['protected_inputs_unchanged'] = False
            record['protection_error'] = type(exc).__name__ + ': ' + str(exc)
        native = output / 'native/native-report.json'
        record['native_status'] = None
        if native.is_file():
            try:
                record['native_status'] = json.loads(native.read_text())['status']
            except BaseException as exc:
                record['native_report_error'] = type(exc).__name__ + ': ' + str(exc)
        passed = (not interrupted and native_exit_passes(record)
                  and record['termination_status'] == 'CHILD_EXIT_CONFIRMED'
                  and record['protected_inputs_unchanged']
                  and record['native_status'] == 'READ_ONLY_SAVED_FRAME_GRAPH_PASS')
        record['status'] = 'GRAPH_INSPECTION_COMPLETE' if passed else 'GRAPH_INSPECTION_INCOMPLETE'
        record['outputs'] = {str(p.relative_to(output)): file_record(p) for p in sorted(output.rglob('*')) if p.is_file()}
        write_new(output / 'process.json', record)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        print(json.dumps({k: record[k] for k in ('status', 'native_exit_code', 'timed_out',
                         'termination_status', 'native_status', 'protected_inputs_unchanged')}, indent=2), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
