"""Run one bounded, CPU2 repository check and preserve its actual outcome."""
import argparse, datetime, hashlib, json, os, signal, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('check',choices=['binding','types','lint','build']);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent/a.check;out.mkdir(exist_ok=True)
assert not (out/'process.json').exists(), 'Keep prior outcomes; use a separate evidence directory for retries'
commands={'binding':['node','scripts/verify-native-wheel-bindings.mjs'],'types':['node','node_modules/typescript/bin/tsc','--noEmit'],'lint':['node','node_modules/oxlint/bin/oxlint','lib/nativeWheelBindings.ts','scripts/verify-native-wheel-bindings.mjs'],'build':['npm','run','build']}
cpus=sorted(os.sched_getaffinity(0))[:2];assert len(cpus)==2
stamp=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
record={'check':a.check,'argv':commands[a.check],'cwd':str(root),'started_utc':stamp(),'cpu_affinity':cpus,'timeout_seconds':120,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
start=time.monotonic();timed_out=False
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
 proc=subprocess.Popen(commands[a.check],cwd=root,stdout=stdout,stderr=stderr,start_new_session=True,preexec_fn=lambda:os.sched_setaffinity(0,cpus))
 try:code=proc.wait(timeout=120)
 except subprocess.TimeoutExpired:
  timed_out=True;os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
record.update(finished_utc=stamp(),elapsed_seconds=time.monotonic()-start,returncode=code,timed_out=timed_out)
for name in ['stdout.log','stderr.log']:
 data=(out/name).read_bytes();record[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(out/'process.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2));raise SystemExit(124 if timed_out else code)
