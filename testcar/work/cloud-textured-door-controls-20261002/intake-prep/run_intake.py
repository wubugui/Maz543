"""One CPU2, 120-second read-only saved-frame door intake. Never starts on import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time


def file_record(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def write_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New direct child directory of this package')
    parser.add_argument('--window-note', required=True, help='Actual concurrent-work context, not an isolated benchmark')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    started = time.monotonic()
    cfg = json.loads((folder / 'inputs/intake.json').read_text())
    checks = json.loads((folder / 'preparation-checks.json').read_text())
    assert checks['status'] == 'PREPARED_NOT_EXECUTED_READY_FOR_REVIEW' and args.window_note.strip()
    prepared = {name: file_record(folder / name) for name in checks['prepared_files']}
    for name, expected in checks['prepared_files'].items():
        assert {key: prepared[name][key] for key in ('bytes', 'sha256')} == expected, name
    prepared['preparation-checks.json'] = file_record(folder / 'preparation-checks.json')
    inputs = {name: file_record(row['path']) for name, row in cfg['inputs'].items()}
    assert inputs == cfg['inputs']
    assert not args.output.exists(), 'Never overwrite an attempt'
    output = args.output.resolve()
    assert output.parent == folder
    budget = cfg['execution']
    assert budget == {'threads': 2, 'wall_seconds': 120, 'postflight_reserve_seconds': 10,
                      'minimum_native_seconds': 60, 'heartbeat_seconds': 10,
                      'term_grace_seconds': 2, 'kill_grace_seconds': 3}
    deadline = started + budget['wall_seconds'] - budget['postflight_reserve_seconds']
    preflight_seconds = time.monotonic() - started
    assert deadline - time.monotonic() >= budget['minimum_native_seconds'], 'Insufficient native budget after preflight'
    cpus = sorted(os.sched_getaffinity(0))[:2]
    assert len(cpus) == 2
    command = ['taskset', '-c', ','.join(map(str, cpus)), inputs['blender']['path'],
               '--background', '--factory-startup', '--disable-autoexec', '--threads', '2',
               '--python-exit-code', '1', '--python', str(folder / 'collect_native.py'), '--',
               '--output', str(output)]
    output.mkdir()
    record = {'status': 'NOT_LAUNCHED', 'phase': cfg['phase'], 'command': command, 'started_utc': utc(),
              'window_note': args.window_note, 'cpu_affinity': cpus, 'budget': budget,
              'inputs_before': inputs, 'prepared_before': prepared, 'timed_out': False,
              'qualification': cfg['qualification'], 'preflight_seconds': preflight_seconds,
              'native_seconds_available': deadline - time.monotonic(),
              'budget_basis': '120s from preflight start;110s latest native terminal observation with10s reserved for postflight. Minimum60s remains before launch. Prior4.5.13 same-source fresh-open12.253s and narrow raw capture12.022s are historical budget context only, not4.5.14 validation. This run reads20 raw door meshes and object/action records without evaluation. Cleanup may add at most5s after a timed-out child; all timing is reported, never a performance claim.'}
    write_json(output / 'launch.json', record)
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    proc, previous = None, {}

    def interrupted(signum, frame):
        raise InterruptedError('Runner received signal ' + str(signum))

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.signal(signum, interrupted)
    try:
        with (output / 'blender.log').open('xb') as log, (output / 'heartbeat.jsonl').open('x') as heartbeat:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            record.update(status='RUNNING', child_pid=proc.pid, owned_process_group=proc.pid)
            write_json(output / 'process.json', record)
            while True:
                code, now = proc.poll(), time.monotonic()
                if code is not None:
                    record['first_terminal_observed_seconds'] = now - started
                    record['timed_out'] = now > deadline
                    break
                try:
                    stage = json.loads((output / 'stage.json').read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    stage = {'stage': 'STARTING'}
                beat = {'utc': utc(), 'elapsed_seconds': now - started, 'stage': stage, 'child_pid': proc.pid}
                heartbeat.write(json.dumps(beat) + '\n')
                heartbeat.flush()
                print(json.dumps(beat), flush=True)
                if now >= deadline:
                    record['timed_out'] = True
                    break
                try:
                    proc.wait(timeout=min(budget['heartbeat_seconds'], deadline - now))
                except subprocess.TimeoutExpired:
                    pass
    except BaseException as exc:
        record['runner_error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        # Block duplicate interruption while writing the true final process state.
        for signum in previous:
            signal.signal(signum, signal.SIG_IGN)
        try:
            if proc is not None and proc.poll() is None:
                # Only this Popen's session. No /proc child scans or unrelated jobs.
                for sig, grace in ((signal.SIGTERM, budget['term_grace_seconds']),
                                   (signal.SIGKILL, budget['kill_grace_seconds'])):
                    try:
                        os.killpg(proc.pid, sig)
                        record.setdefault('cleanup_signals', []).append(sig.name)
                        proc.wait(timeout=grace)
                        break
                    except ProcessLookupError:
                        break
                    except subprocess.TimeoutExpired:
                        continue
        except BaseException as exc:
            record['cleanup_error'] = type(exc).__name__ + ': ' + str(exc)
        record['exit_code'] = proc.poll() if proc is not None else None
        record['child_terminal'] = proc is not None and record['exit_code'] is not None
        record['elapsed_seconds'] = time.monotonic() - started
        record['finished_utc'] = utc()
        record['max_child_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        try:
            record['inputs_after'] = {name: file_record(row['path']) for name, row in inputs.items()}
            record['prepared_after'] = {name: file_record(folder / name) for name in prepared}
            record['file_guards_pass'] = record['inputs_after'] == inputs and record['prepared_after'] == prepared
            native = json.loads((output / 'capture-report.json').read_text())
            record['native_status'] = native['status']
            record['axis_identification'] = native.get('axis_identification')
            record['dependency_blockers'] = native.get('dependency_blockers')
            record['component_summary_complete'] = native.get('component_summary_complete')
            record['legacy_baseline_status'] = native.get('legacy_baseline_comparison', {}).get('status')
            record['installation_eligibility'] = native.get('installation_eligibility')
        except Exception as exc:
            record['final_verification_error'] = type(exc).__name__ + ': ' + str(exc)
        record['elapsed_with_postflight_seconds'] = time.monotonic() - started
        record['operation_deadline_pass'] = record['elapsed_with_postflight_seconds'] <= budget['wall_seconds']
        complete = (record['operation_deadline_pass'] and record['exit_code'] == 0 and record['child_terminal'] and not record['timed_out']
                    and not record.get('runner_error') and not record.get('cleanup_error')
                    and record.get('file_guards_pass') is True
                    and record.get('native_status') == 'CAPTURE_COMPLETE_GUARDS_PASS')
        record['status'] = 'READ_ONLY_CAPTURE_COMPLETE' if complete else 'FAILED_OR_INCOMPLETE'
        write_json(output / 'process.json', record)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(json.dumps({key: record.get(key) for key in
                      ('status', 'exit_code', 'elapsed_seconds', 'axis_identification', 'component_summary_complete')}), flush=True)
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main())
