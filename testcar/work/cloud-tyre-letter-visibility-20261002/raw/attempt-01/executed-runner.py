"""Explicit reviewed launch only; one CPU, 60-second total wall budget.

Preparation does not execute this runner. Unique attempt directories preserve
every failure. Source hash is independently checked even if Blender is killed.
"""
import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--execute-reviewed', action='store_true', required=True)
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
assert args.execute_reviewed and args.attempt.startswith('attempt-') and Path(args.attempt).name == args.attempt
START = time.monotonic()
OUT = ROOT / args.attempt
OUT.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


record = {'status': 'PREFLIGHT', 'process_started': False, 'exit_code': None,
          'hard_total_budget_seconds': 60, 'kill_deadline_from_runner_start_seconds': 57,
          'cleanup_budget_seconds': 3, 'cpu_affinity': [0], 'threads': 1, 'timed_out': False,
          'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'terminal_errors': []}
process = None
plan = None
failed = False
try:
    plan = json.loads((ROOT / 'prepared-plan.json').read_text())
    assert plan['status'] == 'PREPARED_NOT_EXECUTED_REQUIRES_PARENT_REVIEW'
    assert 0 in os.sched_getaffinity(0)
    record['script_sha256'] = sha(ROOT / 'probe-letter-visibility.py')
    record['runner_sha256'] = sha(__file__)
    assert record['script_sha256'] == plan['script_sha256']
    assert record['runner_sha256'] == plan['runner_sha256']
    record['pins_before'] = []
    for item in plan['pins']:
        actual = sha(item['path'])
        record['pins_before'].append({**item, 'actual_sha256': actual})
        assert actual == item['sha256'], ('Pinned input changed', item['path'], actual)
    for source, destination in [('probe-letter-visibility.py', 'executed-script.py'), ('run-bounded.py', 'executed-runner.py')]:
        with (OUT / destination).open('xb') as stream:
            stream.write((ROOT / source).read_bytes())
    with (OUT / 'reviewed-plan.json').open('xb') as stream:
        stream.write((ROOT / 'prepared-plan.json').read_bytes())
    command = [value.replace('{ATTEMPT_DIRECTORY}', str(OUT)) for value in plan['argv_template']]
    record['command'] = command
    write('launch.json', record)
    assert time.monotonic() - START < 56, 'Preflight exhausted budget; no Blender launched'
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='', ONEAPI_DEVICE_SELECTOR='*:cpu')
    with (OUT / 'run.log').open('xb') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        record.update(process_started=True, pid=process.pid, status='RUNNING')
        while True:
            remaining = 57 - (time.monotonic() - START)
            if remaining <= 0:
                record.update(status='TIMED_OUT_PREFIX_PRESERVED', timed_out=True)
                os.killpg(process.pid, signal.SIGKILL)
                record['exit_code'] = process.wait(timeout=1)
                break
            try:
                record['exit_code'] = process.wait(timeout=min(10, remaining))
                record['status'] = 'PROCESS_EXIT_0' if record['exit_code'] == 0 else 'PROCESS_FAILED_PREFIX_PRESERVED'
                break
            except subprocess.TimeoutExpired:
                observation = {'elapsed_seconds': time.monotonic() - START, 'pid': process.pid}
                phase_path = OUT / 'phase.jsonl'
                if phase_path.exists():
                    lines = phase_path.read_text().splitlines()
                    for line in reversed(lines):
                        try:
                            observation['last_complete_phase'] = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue
                with (OUT / 'heartbeat.jsonl').open('a') as stream:
                    stream.write(json.dumps(observation) + '\n')
                print('HEARTBEAT ' + json.dumps(observation), flush=True)
except BaseException as exc:
    failed = True
    record.update(status='RUNNER_FAILED' if record['process_started'] else 'PREFLIGHT_FAILED_NOT_LAUNCHED',
                  error=type(exc).__name__ + ': ' + str(exc))
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            record['exit_code'] = process.wait(timeout=1)
        except BaseException as cleanup:
            record['terminal_errors'].append('kill/wait: ' + repr(cleanup))
finally:
    if plan is not None:
        record['pins_after'] = []
        for item in plan['pins']:
            if item['role'] == 'blender_binary':
                continue
            try:
                actual = sha(item['path'])
                record['pins_after'].append({**item, 'actual_sha256': actual, 'unchanged': actual == item['sha256']})
            except BaseException as exc:
                record['terminal_errors'].append(item['role'] + ': ' + repr(exc))
    try:
        report_path = OUT / 'report.json'
        protection_path = OUT / 'final-protection.json'
        record['report_present'] = report_path.exists()
        record['final_native_matrix_protection_present'] = protection_path.exists()
        if report_path.exists():
            record['native_status'] = json.loads(report_path.read_text())['status']
        if protection_path.exists():
            record['native_protection'] = json.loads(protection_path.read_text())
        else:
            record['native_matrix_protection_status'] = 'UNKNOWN_NOT_COMPLETED'
        record['visibility_prefix_present'] = (OUT / 'visibility-prefix.json').exists()
        record['geometry_prefix_present'] = (OUT / 'geometry-prefix.json').exists()
        record['completed_geometry_files'] = sorted(p.name for p in OUT.glob('geometry-*.json') if p.name != 'geometry-prefix.json')
        record['completed_ray_files'] = sorted(p.name for p in OUT.glob('ray-*.json'))
    except BaseException as exc:
        record['terminal_errors'].append('evidence inventory: ' + repr(exc))
    record.update(elapsed_seconds=time.monotonic() - START,
                  peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    write('process.json', record)
    print(json.dumps(record), flush=True)
if failed or record['terminal_errors'] or any(not p['unchanged'] for p in record.get('pins_after', [])):
    raise SystemExit(2)
if not record['process_started'] or record['exit_code'] is None:
    raise SystemExit(2)
raise SystemExit(124 if record['timed_out'] else record['exit_code'])
