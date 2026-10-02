"""Launch only after explicit parent coordination. CPU2, <=120s total budget."""
import argparse
import hashlib
import json
import os
import resource
import signal
import struct
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path('/workspace/scratch/a29d03198654/Maz543')
VERIFIED_COMMIT = '66085d7f353b6a5ee6d441243f3e0618e2ac0b64'
BASE = REPO / 'testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
BASE_SHA = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
EVIDENCE = REPO / 'testcar/work/cloud-wheel-native-repair-pass-20261002'
SOURCE_PINS = {
    BASE: BASE_SHA,
    EVIDENCE / 'executed-script.py': '5940176455cbb19373f96d0b2150dd636006e67eb73d404e44bf77b9313d49e8',
    EVIDENCE / 'SUMMARY.json': 'cc4a64c3da191351a289100abc6f9a87f0f20204d872e71e9995a6f1331854ac',
    EVIDENCE / 'process.json': '2ba906d3cf8f6000a002a4c96dc5f739d51779b28be3bb1123b8d1a1b7b42244',
    REPO / 'testcar/lib/maz543.ts': 'd1fdc631ff369ab4f7af1c85e828bbd3d053ff35a2ec5291d0d475bbc68f7059',
    REPO / 'testcar/scripts/audit-candidate-cab-static-dependencies.py': '0ca53737b57995ca86bc01612f60175e36cf2199d04edd55017f94ab1c9e1a51',
}
TOOL = '/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender'
parser = argparse.ArgumentParser()
parser.add_argument('--execute-reviewed', action='store_true', required=True)
parser.add_argument('--attempt', default='attempt-01')
args = parser.parse_args()
assert args.execute_reviewed and Path(args.attempt).name == args.attempt and args.attempt.startswith('attempt-')
start = time.monotonic()
out = ROOT / args.attempt
# Fail without touching an existing attempt. Every later step has a terminal.
out.mkdir(exist_ok=False)
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def emit(name, value):
    with (out / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

record = {'status': 'PREFLIGHT_STARTED', 'process_started': False, 'exit_code': None,
          'verified_commit': VERIFIED_COMMIT, 'actual_HEAD': None,
          'actual_HEAD_is_verified_run_commit': False,
          'verification_provenance': 'The completed native verification belongs to verified_commit, not to a later actual_HEAD',
          'threads': 2, 'hard_total_budget_seconds': 120,
          'kill_deadline_seconds_from_runner_start': 117, 'cleanup_budget_seconds': 3,
          'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'timed_out': False,
          'source_file_pins': [], 'terminal_errors': []}
process = None
runner_failed = False
try:
    plan = json.loads((ROOT / 'prepared-plan.json').read_text())
    script = ROOT / 'render-wheel-views.py'
    assert plan['verified_commit'] == VERIFIED_COMMIT
    record['script_sha256'] = sha(script)
    record['runner_sha256'] = sha(__file__)
    assert record['script_sha256'] == plan['render_script_sha256']
    assert record['runner_sha256'] == plan['runner_sha256']
    for path, expected in SOURCE_PINS.items():
        actual = sha(path)
        record['source_file_pins'].append({'path': str(path), 'expected_sha256': expected, 'actual_sha256_before': actual})
        assert actual == expected, ('Pinned input changed', str(path), actual)
    record['source_sha256_before'] = sha(BASE)
    record['actual_HEAD'] = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    record['actual_HEAD_is_verified_run_commit'] = record['actual_HEAD'] == VERIFIED_COMMIT
    ancestor = subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', VERIFIED_COMMIT, record['actual_HEAD']],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    record['verified_commit_is_ancestor_of_actual_HEAD'] = ancestor.returncode == 0
    assert ancestor.returncode == 0, ('Verified commit is not an ancestor of current HEAD', ancestor.returncode, ancestor.stderr)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    assert len(cpus) == 2
    record['cpu_affinity'] = cpus
    with (out / 'executed-script.py').open('xb') as stream:
        stream.write(script.read_bytes())
    with (out / 'executed-runner.py').open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    cmd = ['taskset', '-c', ','.join(map(str, cpus)), TOOL, '--background', '--factory-startup', '--disable-autoexec',
           '--threads', '2', '--python-exit-code', '1', '--python', str(out / 'executed-script.py'), '--', '--output', str(out)]
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='', ONEAPI_DEVICE_SELECTOR='*:cpu')
    record.update(status='PREFLIGHT_PASSED_PROCESS_NOT_STARTED', command=cmd)
    emit('launch.json', record)
    assert time.monotonic() - start < 116, 'Preflight exhausted process budget; Blender was not started'
    with (out / 'run.log').open('xb') as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        record.update(pid=process.pid, process_started=True, status='PROCESS_RUNNING')
        try:
            record['exit_code'] = process.wait(timeout=max(.01, 117 - (time.monotonic() - start)))
            record['status'] = 'PROCESS_COMPLETED' if record['exit_code'] == 0 else 'PROCESS_FAILED'
        except subprocess.TimeoutExpired:
            record.update(timed_out=True, status='PROCESS_TIMED_OUT')
            os.killpg(process.pid, signal.SIGKILL)
            record['exit_code'] = process.wait(timeout=1)
except BaseException as exc:
    runner_failed = True
    record['runner_error'] = type(exc).__name__ + ': ' + str(exc)
    record['status'] = 'RUNNER_FAILED_AFTER_PROCESS_START' if record['process_started'] else 'PREFLIGHT_OR_LAUNCH_FAILED_PROCESS_NOT_STARTED'
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            record['exit_code'] = process.wait(timeout=1)
        except BaseException as cleanup_exc:
            record['terminal_errors'].append('Process termination: ' + repr(cleanup_exc))
finally:
    try:
        record['source_sha256_after'] = sha(BASE)
        record['source_unchanged'] = record['source_sha256_after'] == BASE_SHA
    except BaseException as exc:
        record['source_unchanged'] = None
        record['terminal_errors'].append('Source hash read: ' + repr(exc))
    record['views'] = []
    for label in ['neutral', 'spin-0p731']:
        try:
            terminal = out / (label + '-terminal.json')
            if terminal.exists():
                view = json.loads(terminal.read_text())
            else:
                view = {'view': label, 'status': ('PROCESS_TIMED_OUT_DURING_VIEW' if record['timed_out'] else 'PROCESS_ENDED_WITHOUT_VIEW_TERMINAL')
                        if (out / (label + '-start.json')).exists() else 'NOT_STARTED',
                        'process_started': record['process_started'], 'finally_restoration_confirmed': False}
                emit(label + '-process-terminal.json', view)
            png = out / ('wheel-' + label + '.png')
            if png.exists():
                raw = png.read_bytes()
                view['runner_png_check'] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                            'dimensions': list(struct.unpack('>II', raw[16:24])) if raw[:8] == b'\x89PNG\r\n\x1a\n' else None}
            record['views'].append(view)
        except BaseException as exc:
            record['terminal_errors'].append(label + ' finalization: ' + repr(exc))
            record['views'].append({'view': label, 'status': 'TERMINAL_RECORD_READ_FAILED', 'error': repr(exc)})
    record.update(elapsed_seconds=time.monotonic() - start,
                  peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    emit('process.json', record)
    print(json.dumps(record), flush=True)
if runner_failed or record['terminal_errors'] or record.get('source_unchanged') is not True:
    raise SystemExit(2)
if not record['process_started'] or record['exit_code'] is None:
    raise SystemExit(2)
raise SystemExit(124 if record['timed_out'] else record['exit_code'])
