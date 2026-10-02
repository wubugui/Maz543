"""One bounded pure-Python command, terminal evidence retained even on failure."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('diagnosis', 'tests'))
    args = parser.parse_args()
    cfg = json.loads((HERE.parent / 'cloud-ten-normal-capture-20261002/capture.json').read_text())
    assert Path(sys.executable).resolve() == Path(cfg['inputs']['bundled_python']['path']).resolve()
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2')
    command = [sys.executable, '-B', str(HERE / ('classify_normals.py' if args.mode == 'diagnosis' else 'test_classification.py'))]
    if args.mode == 'diagnosis':
        command += ['--output', str(HERE / 'attempt-02/classification.json')]
    prefix = HERE / 'attempt-02' / args.mode
    terminal_path, log_path = Path(str(prefix) + '-terminal.json'), Path(str(prefix) + '.log')
    assert not terminal_path.exists() and not log_path.exists()
    started = datetime.now(timezone.utc).isoformat(); start = time.monotonic()
    timed_out = False
    with log_path.open('xb') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        try:
            code = child.wait(timeout=27)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait(timeout=2)
    terminal = {'argv': command, 'started_at_utc': started, 'ended_at_utc': datetime.now(timezone.utc).isoformat(),
                'elapsed_seconds': time.monotonic() - start, 'timeout_seconds': 27, 'timed_out': timed_out,
                'actual_exit_code': code, 'cpu_affinity': sorted(os.sched_getaffinity(0)),
                'python': sys.version, 'log_bytes': log_path.stat().st_size,
                'log_sha256': hashlib.sha256(log_path.read_bytes()).hexdigest(),
                'status': 'COMPLETED' if code == 0 and not timed_out else 'FAILED'}
    with terminal_path.open('x') as out:
        json.dump(terminal, out, indent=2); out.write('\n')
    print(json.dumps(terminal))
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    raise SystemExit(main())
