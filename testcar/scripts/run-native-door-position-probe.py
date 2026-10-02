import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import resource
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--blender', required=True)
p.add_argument('--source', required=True)
p.add_argument('--scripts', required=True)
p.add_argument('--decoder-dir', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=False)
names = ['probe-native-door-position-precision.py', 'read-door-grid-probe.mjs', 'cab-door-position-precision.mjs']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in names: shutil.copyfile(Path(a.scripts) / name, out / name)
shutil.copyfile(__file__, out / 'executed-runner.py')
frozen = {name: sha(out / name) for name in names + ['executed-runner.py']}
argv = [a.blender, '--background', '--factory-startup', '--disable-autoexec', '--threads', '1',
        '--python-exit-code', '1', '--python', str(out / names[0]), '--', '--source', a.source,
        '--out', str(out), '--grid-reader', str(out / names[1]), '--decoder-dir', a.decoder_dir]
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', BLIS_NUM_THREADS='1')
record = {'argv': argv, 'deadlineSeconds': 120, 'scriptSHA256Before': frozen, 'sourceSHA256Before': sha(a.source)}
(out / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
start = time.monotonic()
with (out / 'native.log').open('wb') as log:
    try:
        process = subprocess.Popen(argv, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        record['exitCode'] = process.wait(timeout=120)
        record['timedOut'] = False
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        record['exitCode'] = process.returncode
        record['timedOut'] = True
record['elapsedSeconds'] = time.monotonic() - start
record['peakChildRssKiB'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
record['resourceMeaning'] = 'Linux RUSAGE_CHILDREN ru_maxrss for this runner; not aggregate concurrent memory or isolated performance benchmark'
record['sourceSHA256After'] = sha(a.source)
record['scriptSHA256After'] = {name: sha(out / name) for name in names + ['executed-runner.py']}
record['outputs'] = {file.name: {'bytes': file.stat().st_size, 'sha256': sha(file)} for file in out.iterdir()
                     if file.is_file() and file.name not in names}
(out / 'process.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'exitCode': record['exitCode'], 'timedOut': record['timedOut'], 'elapsedSeconds': record['elapsedSeconds']}))
raise SystemExit(0 if record['exitCode'] == 0 and not record['timedOut'] else 1)
