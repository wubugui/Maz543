import hashlib,json,os,resource,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'appearance-components-01';out.mkdir(exist_ok=False);repo=Path('/workspace/scratch/a29d03198654/Maz543');base=repo/'testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend';tool='/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender';script=root/'read-appearance-components.py';script_bytes=script.read_bytes();(out/'executed-script.py').write_bytes(script_bytes);(out/'executed-runner.py').write_bytes(Path(__file__).read_bytes());cpu=min(os.sched_getaffinity(0))
cmd=['taskset','-c',str(cpu),tool,'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','1','--python',str(out/'executed-script.py'),'--','--base',str(base),'--sha','8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70','--output',str(out)]
env=dict(os.environ);env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');start=time.monotonic();r={'command':cmd,'cpu_affinity':[cpu],'hard_timeout_seconds':30,'script_sha256':hashlib.sha256(script_bytes).hexdigest(),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};(out/'launch.json').write_text(json.dumps(r,indent=2)+'\n')
try:
 with (out/'run.log').open('wb') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=30)
 r['exit_code']=p.returncode
except subprocess.TimeoutExpired:r['timed_out']=True;r['exit_code']=None
r.update(elapsed_seconds=time.monotonic()-start,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));(out/'process.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
raise SystemExit(r['exit_code'] if r['exit_code'] is not None else 124)
