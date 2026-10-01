"""Portable one-shot 180-second runner for the conditional 140-head sweep.

Requires an existing official Blender 4.5.13 and the pinned repository inputs.
The requested output directory must be new and outside the repository.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,resource,subprocess,time,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--blender',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--script',type=Path,default=Path(__file__).with_name('audit-repaired-head-sweep.py'))
a=p.parse_args()
repo,blender,out,script=(x.resolve() for x in (a.repo,a.blender,a.out,a.script))
assert not out.is_relative_to(repo),'Output must stay outside the repository'
assert repo.is_dir() and blender.is_file() and script.is_file()
source=repo/'testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert sha(source)=='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(script)=='2c4b722bbff47caa2a73dd46c04027da6f2a829e408f81d74dbfb6532a424fc0'
out.mkdir(parents=True,exist_ok=False)
cmd=[str(blender),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','1','--python',str(script),'--','--repo',str(repo),'--out',str(out)]
record={'status':'IN_PROGRESS_NOT_ACCEPTED','started_utc':now(),'command':cmd,'cwd':str(out.parent),'timeout_seconds':180,
 'source_sha256_before':sha(source),'script_sha256_before':sha(script),'runner_sha256':sha(Path(__file__)),
 'blender_binary_sha256':sha(blender),'source_bytes':source.stat().st_size,'claims_isolated_performance':False}
process_file=out/'process.json'
process_file.write_text(json.dumps(record,indent=2)+'\n')
start=time.monotonic();timed_out=False
with (out/'read.log').open('wb') as log:
 process=subprocess.Popen(cmd,cwd=out.parent,stdout=log,stderr=subprocess.STDOUT)
 record['owned_blender_pid']=process.pid;process_file.write_text(json.dumps(record,indent=2)+'\n')
 try:returncode=process.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;process.kill();returncode=process.wait()
record.update({'status':'COMPLETED' if returncode==0 and not timed_out else 'FAILED_OR_TIMED_OUT',
 'finished_utc':now(),'elapsed_seconds':time.monotonic()-start,'returncode':returncode,'timed_out':timed_out,
 'peak_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
 'source_sha256_after':sha(source),'script_sha256_after':sha(script),'read_log_sha256':sha(out/'read.log')})
record['source_unchanged']=record['source_sha256_before']==record['source_sha256_after']
record['script_unchanged']=record['script_sha256_before']==record['script_sha256_after']
record['artifacts']={str(f.relative_to(out)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file() and f!=process_file}
process_file.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
sys.exit(0 if returncode==0 and not timed_out and record['source_unchanged'] and record['script_unchanged'] else 1)
