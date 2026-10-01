import argparse,subprocess,time,json,hashlib,os,signal,resource,shutil,datetime
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('--script',required=True);P.add_argument('--name',required=True);P.add_argument('args',nargs=argparse.REMAINDER);a=P.parse_args()
D=Path(__file__).resolve().parent;script=Path(a.script).resolve();frozen=D/(a.name+'-executed-script.py');assert not frozen.exists();shutil.copyfile(script,frozen)
blender=Path('/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender');source=Path('/workspace/scratch/a29d03198654/maz-native-axis-controls-20261001/MAZ543A_Native_Barrel_Axis_Controls.blend');original=Path('/workspace/scratch/a29d03198654/Maz543/testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before={str(p):sha(p) for p in [blender,source,original,script,frozen]};log=D/(a.name+'.log');receipt=D/(a.name+'-process.json');assert not log.exists() and not receipt.exists()
cmd=[str(blender),'--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','17','--python',str(frozen),'--']+(a.args[1:] if a.args and a.args[0]=='--' else a.args)
env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2');start=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();timeout=False
with log.open('wb') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=D,env=env,start_new_session=True)
 try:code=p.wait(timeout=240)
 except subprocess.TimeoutExpired:
  timeout=True;os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);code=p.wait()
elapsed=time.monotonic()-start;after={str(p):sha(p) for p in [source,original,script,frozen]};outputs={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in D.rglob('*') if p.is_file() and p.suffix in {'.json','.png'} and p!=receipt}
r={'command':cmd,'cpu_threads':2,'deadline_s':240,'timed_out':timeout,'exit_code':code,'elapsed_s':elapsed,'start_utc_system_clock':utc,'peak_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'input_sha256':before,'post_sha256':after,'candidate_source_unchanged':before[str(source)]==after[str(source)],'original_source_unchanged':before[str(original)]==after[str(original)],'executed_script_unchanged':before[str(frozen)]==after[str(frozen)],'log':log.name,'log_sha256':sha(log),'outputs_at_exit':outputs};receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(code if code>=0 else 128-code)
