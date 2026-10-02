"""One fresh, bounded offline GLB view. This module never starts on import."""
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
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--view', choices=('overview', 'side'), required=True)
    parser.add_argument('--output', type=Path, required=True, help='New direct child directory of this package')
    parser.add_argument('--window-note', required=True, help='Actual concurrent-work context; not an isolated benchmark')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    cfg = json.loads((folder / 'observation.json').read_text())
    checks = json.loads((folder / 'preparation-checks.json').read_text())
    assert checks['status'] == 'PREPARED_NOT_EXECUTED'
    assert args.window_note.strip()
    prepared_before = {name: file_record(folder / name) for name in checks['prepared_files']}
    for name, expected in checks['prepared_files'].items():
        assert {key: prepared_before[name][key] for key in ('bytes', 'sha256')} == expected, name
    prepared_before['preparation-checks.json'] = file_record(folder / 'preparation-checks.json')
    input_before = file_record(cfg['input']['path'])
    assert input_before == cfg['input'], 'GLB differs from the restored published input'
    blender_before = file_record(cfg['blender']['path'])
    assert blender_before['sha256'] == cfg['blender']['sha256'], 'Official Blender binary changed'
    assert not args.output.exists(), 'Never overwrite a previous attempt'
    output = args.output.resolve()
    assert output.parent == folder, 'Output must be a new direct child of this package'
    output.mkdir()
    cpus = sorted(os.sched_getaffinity(0))[:2]
    assert len(cpus) == cfg['render']['threads'] == 2
    budget = cfg['execution']
    assert budget == {'wall_seconds_per_view': 900, 'heartbeat_seconds': 10,
                      'term_grace_seconds': 5, 'kill_grace_seconds': 5}
    command = ['taskset', '-c', ','.join(map(str, cpus)), cfg['blender']['path'],
               '--background', '--factory-startup', '--disable-autoexec', '--threads', '2',
               '--python-exit-code', '1', '--python', str(folder / 'observe_glb.py'), '--',
               '--view', args.view, '--output', str(output)]
    record = {'title': cfg['title'], 'status': 'NOT_LAUNCHED', 'view': args.view,
              'command': command, 'started_utc': utc(), 'window_note': args.window_note,
              'cpu_affinity': cpus, 'budget': budget, 'input_before': input_before,
              'blender_before': blender_before, 'prepared_before': prepared_before,
              'qualification': cfg['qualification'], 'timed_out': False,
              'budget_basis': 'One 134MB GLB import, finite guards, CPU2 BVH and one 1024x640 16-sample Cycles image. 900s is an operational ceiling, not a performance prediction or acceptance result.',
              'performance_claim': 'Elapsed time includes actual concurrent resource contention'}
    write_json(output / 'launch.json', record)
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2',
               PYTHONDONTWRITEBYTECODE='1')
    proc = None
    start = time.monotonic()
    deadline = start + budget['wall_seconds_per_view']
    previous = {}

    def interrupted(signum, frame):
        raise InterruptedError('Runner received signal ' + str(signum))

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.signal(signum, interrupted)
    try:
        with (output / 'blender.log').open('xb') as log, (output / 'heartbeat.jsonl').open('x') as heartbeat:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                    env=env, start_new_session=True)
            record.update(status='RUNNING', child_pid=proc.pid, owned_process_group=proc.pid)
            write_json(output / 'process.json', record)
            while True:
                code = proc.poll()
                now = time.monotonic()
                if code is not None:
                    record['first_terminal_observed_seconds'] = now - start
                    record['timed_out'] = now > deadline
                    break
                try:
                    stage = json.loads((output / 'stage.json').read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    stage = {'stage': 'STARTING'}
                beat = {'utc': utc(), 'elapsed_seconds': now - start, 'stage': stage, 'child_pid': proc.pid}
                heartbeat.write(json.dumps(beat, ensure_ascii=False) + '\n')
                heartbeat.flush()
                print(json.dumps(beat, ensure_ascii=False), flush=True)
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
        for signum in previous:
            signal.signal(signum, signal.SIG_IGN)
        # This session belongs only to this Popen. Never enumerate or signal other jobs.
        if proc is not None and proc.poll() is None:
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
        record['exit_code'] = proc.poll() if proc is not None else None
        record['child_terminal'] = proc is not None and record['exit_code'] is not None
        record['elapsed_seconds'] = time.monotonic() - start
        record['finished_utc'] = utc()
        record['max_child_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        try:
            record['input_after'] = file_record(cfg['input']['path'])
            record['blender_after'] = file_record(cfg['blender']['path'])
            record['prepared_after'] = {name: file_record(folder / name) for name in prepared_before}
            record['file_guards_pass'] = (record['input_after'] == input_before
                                          and record['blender_after'] == blender_before
                                          and record['prepared_after'] == prepared_before)
            native = json.loads((output / 'observation-report.json').read_text())
            record['native_status'] = native['status']
            record['image'] = native.get('image')
        except Exception as exc:
            record['final_verification_error'] = type(exc).__name__ + ': ' + str(exc)
        passed = (record['exit_code'] == 0 and not record['timed_out'] and not record.get('runner_error')
                  and record.get('file_guards_pass') is True
                  and record.get('native_status') == 'OFFLINE_OBSERVATION_RENDERED_GUARDS_PASS')
        record['status'] = 'OFFLINE_OBSERVATION_COMPLETE' if passed else 'FAILED_OR_INCOMPLETE'
        write_json(output / 'process.json', record)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(json.dumps({'status': record['status'], 'exit_code': record['exit_code'],
                      'elapsed_seconds': record['elapsed_seconds'], 'output': str(output)}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
