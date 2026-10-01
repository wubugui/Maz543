import subprocess,pathlib,hashlib,time,json,resource,datetime,sys
W=pathlib.Path(__file__).resolve().parent
B=W.parent/'maz543-tools/blender-4.5.13-linux-x64/blender';S=pathlib.Path(sys.argv[1]).resolve(); tag=sys.argv[2]; extra=sys.argv[3:]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=W.parent/'Maz543/testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
cmd=[str(B),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','17','--python',str(S),'--',*extra]
r={'status':'IN_PROGRESS','command':cmd,'script_sha256_before':sha(S),'source_sha256_before':sha(source),'blender_binary_sha256':sha(B),'deadline_seconds':240,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'not_isolated_performance':True};p=W/(tag+'-process.json');p.write_text(json.dumps(r,indent=2)+'\n');start=time.monotonic()
try:
 with (W/(tag+'.log')).open('wb') as f:out=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 r.update(status='EXITED',exit_code=out.returncode)
except subprocess.TimeoutExpired:r.update(status='TIMEOUT',exit_code=None)
r.update(elapsed_seconds=time.monotonic()-start,max_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,script_sha256_after=sha(S),source_sha256_after=sha(source),log_sha256=sha(W/(tag+'.log')),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(0 if r.get('exit_code')==0 else 1)
