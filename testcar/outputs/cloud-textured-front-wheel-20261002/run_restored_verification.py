"""Bounded fresh-open of exact bytes recovered from the published Git parts."""
import argparse, hashlib, json, os, resource, subprocess, time
from pathlib import Path

p = argparse.ArgumentParser()
for name in ('artifact', 'evidence', 'manifest', 'blender', 'out'):
    p.add_argument('--' + name, type=Path, required=True)
p.add_argument('--window-note', required=True)
a = p.parse_args()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert a.window_note.strip()
assert sha(a.blender) == 'e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe'
assert a.artifact.stat().st_size == 100052636
assert sha(a.artifact) == '48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea'
script = Path(__file__).with_name('verify_restored_native.py')
compile(script.read_bytes(), str(script), 'exec')
protected = [a.artifact, a.manifest, script, Path(__file__)]
protected += sorted(x for x in a.evidence.rglob('*') if x.is_file())
before = {str(x.resolve()): sha(x) for x in protected}
a.out.mkdir(parents=True, exist_ok=False)
cpus = sorted(os.sched_getaffinity(0))[:2]
cmd = ['taskset', '-c', ','.join(map(str, cpus)), str(a.blender),
       '--background', '--factory-startup', '--disable-autoexec', '--threads', '2',
       '--python-exit-code', '1', '--python', str(script), '--',
       '--artifact', str(a.artifact), '--evidence', str(a.evidence),
       '--manifest', str(a.manifest), '--output', str(a.out / 'native-report.json')]
record = {'status': 'RUNNING', 'command': cmd, 'window_note': a.window_note,
          'child_budget_seconds': 60, 'cleanup_budget_seconds': 3,
          'cpu_affinity': cpus, 'protected_before': before,
          'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
          'original_cloud_model_not_used': True, 'saved_model': False, 'rendered': False}
(a.out / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
env = dict(os.environ)
env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2')
proc = None
start = time.monotonic()
try:
    with (a.out / 'run.log').open('xb') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        proc.wait(timeout=60)
    record.update(exit_code=proc.returncode, timed_out=False)
except subprocess.TimeoutExpired:
    record.update(exit_code=None, timed_out=True)
except BaseException as exc:
    record.update(exit_code=None, error=type(exc).__name__ + ': ' + str(exc))
finally:
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        except BaseException as exc:
            record['cleanup_error'] = type(exc).__name__ + ': ' + str(exc)
    record.update(termination_status='NOT_LAUNCHED' if proc is None else
                  'CHILD_EXIT_CONFIRMED' if proc.poll() is not None else 'TERMINATION_UNCONFIRMED',
                  elapsed_seconds=time.monotonic() - start,
                  peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    record['protected_after'] = {str(x.resolve()): sha(x) for x in protected}
    native = a.out / 'native-report.json'
    record['native_status'] = json.loads(native.read_text())['status'] if native.exists() else None
    passed = (record.get('exit_code') == 0 and record['termination_status'] == 'CHILD_EXIT_CONFIRMED'
              and record['native_status'] == 'REMOTE_RESTORED_NATIVE_FRESH_OPEN_PASS'
              and record['protected_after'] == before)
    record['status'] = 'REMOTE_NATIVE_VERIFICATION_COMPLETE' if passed else 'REMOTE_NATIVE_VERIFICATION_INCOMPLETE'
    (a.out / 'process.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if not k.startswith('protected_')}, indent=2), flush=True)
raise SystemExit(0 if passed else 1)
