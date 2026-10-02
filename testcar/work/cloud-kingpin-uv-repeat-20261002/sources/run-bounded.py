"""Default is preflight only. --execute additionally requires an explicit handoff note.

The local PID namespace cannot establish exclusion of other cloud tasks. An
exclusive native-compute window on the shared cloud computer must be confirmed
before invoking --execute.
"""
import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--execute', action='store_true')
p.add_argument('--handoff-note', help='Record of the confirmed exclusive native-compute window on the shared cloud computer; no new user approval is required')
p.add_argument('--output-name', default='repeat-01')
a = p.parse_args()
root = Path(__file__).resolve().parent
inputs = root / 'inputs.json'
script = root / 'inspect-repeat.py'
manifest = json.loads((root / 'PREPARATION-MANIFEST.json').read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
for n, entry in manifest['prepared_files'].items():
    path = root / n
    assert path.stat().st_size == entry['bytes'] and sha(path.read_bytes()) == entry['sha256'], n
I = json.loads(inputs.read_text())
source = Path(I['source_path'])
tool = Path(I['blender_path'])
assert source.stat().st_size == I['source_bytes'] and sha(source.read_bytes()) == I['source_sha256']
assert sha(tool.read_bytes()) == I['blender_executable_sha256']
compile(script.read_text(), str(script), 'exec')
observed = subprocess.run(['ps', '-eo', 'pid=,comm='], capture_output=True, text=True, check=True)
blender_observation = [x.strip() for x in observed.stdout.splitlines() if x.split() and x.split()[-1] == 'blender']
preflight = {'status': 'PREPARED_NOT_EXECUTED', 'source_sha256': I['source_sha256'],
             'prepared_script_sha256': sha(script.read_bytes()), 'visible_namespace_blender_rows': blender_observation,
             'exclusive_access_verified': False,
             'namespace_limit': 'This observation cannot see other cloud-task PID namespaces or establish exclusive engine access.',
             'required_next_action': 'Confirm the exclusive native-compute window; then run --execute --handoff-note UTC_WINDOW_CONFIRMATION.'}
if not a.execute:
    print(json.dumps(preflight, ensure_ascii=False, indent=2))
    raise SystemExit(0)
assert a.handoff_note and a.handoff_note.strip(), 'An exclusive native-compute window record is required; elapsed time is not window confirmation.'
assert not blender_observation, 'Blender observed in this namespace; stop without terminating it.'
assert Path(a.output_name).name == a.output_name and a.output_name not in {'', '.', '..'}
out = root / a.output_name
out.mkdir(exist_ok=False)
for name in [*manifest['prepared_files'], 'PREPARATION-MANIFEST.json']:
    (out / name).write_bytes((root / name).read_bytes())
cpu = min(os.sched_getaffinity(0))
cmd = ['taskset', '-c', str(cpu), str(tool), '--background', '--factory-startup', '--disable-autoexec',
       '--threads', '1', '--python-exit-code', '1', '--python', str(out / script.name), '--',
       '--inputs', str(out / inputs.name), '--output', str(out)]
env = dict(os.environ)
env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
record = {'status': 'RUNNING', 'command': cmd, 'child_execution_timeout_seconds': 120,
          'cleanup_budget_seconds': 3, 'process_control_budget_seconds': 123,
          'budget_scope': 'Child execution plus termination waits; final source hashing/report I/O are outside this process-control budget.',
          'exit_code': None, 'timed_out': False, 'cpu_affinity': [cpu],
          'handoff_note': a.handoff_note, 'exclusive_access_verified_by_pid_scan': False,
          'visible_namespace_blender_rows_before_launch': blender_observation,
          'source_sha256_before': I['source_sha256'], 'script_sha256': sha(script.read_bytes()),
          'inputs_sha256': sha(inputs.read_bytes()), 'runner_sha256': sha(Path(__file__).read_bytes()),
          'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
(out / 'launch.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
start = time.monotonic()
complete = False
proc = None
try:
    with (out / 'run.log').open('xb') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        record['launched_child_pid_in_this_namespace'] = proc.pid
        while True:
            remaining = 120 - (time.monotonic() - start)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(cmd, 120)
            try:
                proc.wait(timeout=min(12, remaining))
                break
            except subprocess.TimeoutExpired:
                with (out / 'heartbeat.jsonl').open('a') as heartbeat:
                    heartbeat.write(json.dumps({'elapsed_seconds': time.monotonic() - start,
                        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'log_bytes': (out / 'run.log').stat().st_size,
                        'native_report_present': (out / 'native-report.json').exists()}) + '\n')
    record['exit_code'] = proc.returncode
    record['timed_out'] = False
except subprocess.TimeoutExpired:
    record.update(exit_code=None, timed_out=True)
except Exception as exc:
    record.update(exit_code=None, timed_out=False, launch_error=type(exc).__name__ + ': ' + str(exc))
finally:
    if proc is not None and proc.poll() is None:
        # Own Popen handle only; never terminate any process discovered by ps.
        cleanup_start = time.monotonic()
        cleanup_deadline = cleanup_start + 3
        try:
            proc.terminate()
            try:
                proc.wait(timeout=min(1, max(.001, cleanup_deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                proc.kill()
                remaining_cleanup = cleanup_deadline - time.monotonic()
                if remaining_cleanup > 0:
                    proc.wait(timeout=remaining_cleanup)
        except Exception as exc:
            record['cleanup_error'] = type(exc).__name__ + ': ' + str(exc)
        record['cleanup_elapsed_seconds'] = time.monotonic() - cleanup_start
        record['cleanup_child_exit_code'] = proc.returncode
    record['termination_status'] = 'NOT_LAUNCHED' if proc is None else 'CHILD_EXIT_CONFIRMED' if proc.poll() is not None else 'TERMINATION_UNCONFIRMED'
    record.update(elapsed_seconds=time.monotonic() - start,
                  peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        record['source_sha256_after'] = sha(source.read_bytes())
    except Exception as exc:
        record['source_sha256_after'] = None
        record['source_final_read_error'] = type(exc).__name__ + ': ' + str(exc)
    native = out / 'native-report.json'
    record['native_report_present'] = native.exists()
    record['native_status'] = None
    try:
        if native.exists():
            record['native_status'] = json.loads(native.read_text())['status']
    except Exception as exc:
        record['native_report_read_error'] = type(exc).__name__ + ': ' + str(exc)
    record['source_unchanged'] = record['source_sha256_after'] == I['source_sha256']
    complete = record['exit_code'] == 0 and record['termination_status'] == 'CHILD_EXIT_CONFIRMED' and record['source_unchanged'] and record['native_status'] in {'UV_CHANGE_REPRODUCED_NO_ACCEPTANCE', 'UV_CHANGE_NOT_REPRODUCED_IN_THIS_RUN'}
    record['status'] = 'TERMINATION_UNCONFIRMED' if record['termination_status'] == 'TERMINATION_UNCONFIRMED' else 'DIAGNOSTIC_CAPTURE_COMPLETE' if complete else 'TIMEOUT_INCOMPLETE' if record.get('timed_out') else 'DIAGNOSTIC_CAPTURE_INCOMPLETE'
    (out / 'process.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)
raise SystemExit(0 if complete else 124 if record.get('timed_out') else 1)
