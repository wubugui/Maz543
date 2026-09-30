import sys,json,zipfile,uuid,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(r'C:\Users\weiruanrinima\.codex\skills\inference-hub-generation\scripts')))
from hub_client import HubClient
root=Path(__file__).resolve().parents[2];work=Path(__file__).resolve().parent
client=HubClient('http://denghong01:8765',app_id='codex',project_id='maz543a')
record_path=work/'audit-task-record.json'
if record_path.exists():
    record=json.loads(record_path.read_text(encoding='utf8'))
else:
    package=work/'searchlight-audit.zip'
    hashes={}
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        z.write(work/'main.py','main.py')
        for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
            file=root/'outputs'/name;z.write(file,name);hashes[name]=hashlib.sha256(file.read_bytes()).hexdigest()
    record={'base_url':'http://denghong01:8765','idempotency_key':'maz543a-searchlight-audit-'+uuid.uuid4().hex,'source_sha256':hashes}
    record_path.write_text(json.dumps(record,indent=2),encoding='utf8')
    upload=client.upload(package)
    record['project_file']=upload['id']
    record_path.write_text(json.dumps(record,indent=2),encoding='utf8')
if 'response' not in record:
    if 'project_file' not in record:raise RuntimeError('Resume the saved upload from stdout before submitting')
    body={'backend':'blender','name':'MAZ543A roof searchlight native audit','priority':50,'params':{'version':'4.5.13','project_file':record['project_file'],'script':'main.py','device':'cpu','threads':4,'ram_mb':8192,'timeout_seconds':600}}
    record['body']=body;record_path.write_text(json.dumps(record,indent=2),encoding='utf8')
    record['response']=client.call('POST','/v1/tasks',json=body,headers={'Idempotency-Key':record['idempotency_key']})
    record_path.write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record['response']),flush=True)
