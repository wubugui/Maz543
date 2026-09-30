"""Append the last conversation delta and safely remove temporary junctions."""
import collections,datetime,hashlib,json,os,shutil,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;ZIP=OUT/'MAZ543_COMPLETE_20260906.zip'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p,limit=None):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while limit is None or limit>0:
   b=f.read(4*1024*1024 if limit is None else min(limit,4*1024*1024))
   if not b:break
   h.update(b)
   if limit is not None:limit-=len(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
report=json.loads((OUT/'VERIFIED.json').read_text(encoding='utf-8'));assert report['passed']
assert sha(ZIP)==report['archive_sha256']
tree=OUT/'archive-tree';removed=[]
for item in json.loads((OUT/'temporary-junctions.json').read_text(encoding='utf-8')):
 link=Path(item['link']);expected=Path(item['target']).resolve()
 assert link.absolute().is_relative_to(tree.absolute())
 assert link.is_junction() and link.resolve()==expected and expected.exists()
 os.rmdir(link)  # RemoveDirectoryW deletes this junction only, never its target.
 assert expected.exists();removed.append(str(link))
assert tree.resolve().is_relative_to(OUT.resolve())
for d,ds,fs in os.walk(tree):
 for n in ds+fs:
  p=Path(d)/n;assert not p.is_junction() and not p.is_symlink();assert p.resolve().is_relative_to(OUT.resolve())
shutil.rmtree(tree)  # Only verified local temporary copies remain here.
dump(OUT/'TEMPORARY_LAYOUT_REMOVED.json',dict(time=now(),removed_junctions=removed,source_targets_preserved=True))
latest=OUT/'latest-history';latest.mkdir(exist_ok=True);index=[];additions=[]
base=json.loads((OUT/'support/conversation/history-index.json').read_text(encoding='utf-8'))
for r in base:
 src=Path(r['source']);assert sha(src,r['bytes'])==r['sha256']
 size=src.stat().st_size
 with src.open('rb') as f:f.seek(r['bytes']);delta=f.read(size-r['bytes'])
 records=[json.loads(line) for line in delta.splitlines() if line.strip()]
 ords=[x['ordinal'] for x in records if 'ordinal'in x]
 assert all(b==a+1 for a,b in zip(ords,ords[1:]))
 name=r['thread_id']+'.delta.jsonl';p=latest/name;p.write_bytes(delta)
 additions.append((p,'conversation/latest-deltas/'+name))
 index.append(dict(thread_id=r['thread_id'],base='conversation/'+r['file'],base_bytes=r['bytes'],base_sha256=r['sha256'],delta='conversation/latest-deltas/'+name,delta_bytes=len(delta),delta_sha256=sha(p),delta_records=len(records),first_ordinal=ords[0] if ords else None,last_ordinal=ords[-1] if ords else None,last_timestamp=records[-1].get('timestamp') if records else r['last_timestamp'],captured_utc=now(),combined_bytes=size,combined_sha256=sha(src,size)))
dump(latest/'index.json',index);additions.append((latest/'index.json','conversation/latest-deltas/index.json'))
note=latest/'READ_ME.md';note.write_text('# 最后对话补档\n\n主原始记录已在 conversation/raw 中完整保存。本目录 delta 文件从主记录快照的精确字节末尾继续，包含后续打包、排错与校验对话；将对应 raw 文件与 delta 按字节连接即可恢复至 index.json 标注的最终捕获时点。\n\n索引保存原快照与补档各自 SHA-256、字节数和合并后的 SHA-256。捕获时点之后的最终交付消息不在快照内。所有文件与主模型都在同一个 ZIP 内。\n',encoding='utf-8');additions.append((note,'conversation/latest-deltas/READ_ME.md'))
additions.append((Path(__file__),'migration/finalize-backup.py'))
entries=[dict(path=n,size=p.stat().st_size,sha256=sha(p)) for p,n in additions]
extra=latest/'FINAL_ADDITIONS.json';dump(extra,dict(created_utc=now(),entries=entries));additions.append((extra,'migration/FINAL_ADDITIONS.json'))
with zipfile.ZipFile(ZIP) as z:
 offset=z.start_dir
 old={i.filename:(i.header_offset,i.CRC,i.file_size,i.compress_size,i.compress_type) for i in z.infolist()}
prefix_hash=sha(ZIP,offset)
recovery=OUT/'verified-base-before-final.zip';shutil.copy2(ZIP,recovery)
with zipfile.ZipFile(ZIP,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for p,name in additions:
  assert name not in old;z.write(p,name)
assert sha(ZIP,offset)==prefix_hash
with zipfile.ZipFile(ZIP) as z:
 infos=z.infolist();assert len({i.filename for i in infos})==len(infos)
 for i in infos:
  if i.filename in old:assert old[i.filename]==(i.header_offset,i.CRC,i.file_size,i.compress_size,i.compress_type)
 for p,name in additions:assert hashlib.sha256(z.read(name)).hexdigest()==sha(p)
 total_files=sum(not i.is_dir() for i in infos)
hash_final=sha(ZIP)
report.update(verified_utc=now(),archive_bytes=ZIP.stat().st_size,archive_sha256=hash_final,base_verified_source_files=report['verified_files'],total_archive_files=total_files,final_history_index=index,final_additions=len(additions),base_archive_data_prefix_unchanged=True,method=report['method']+'; final conversation delta appended; all original compressed data prefix and member descriptors unchanged; every addition CRC32/SHA-256 verified')
dump(OUT/'VERIFIED.json',report)
(OUT/(ZIP.name+'.sha256')).write_text(hash_final+'  '+ZIP.name+'\n',encoding='ascii')
assert recovery.resolve().parent==OUT.resolve();recovery.unlink()
(OUT/'BACKUP_COMPLETE.txt').write_text('BACKUP COMPLETE\n'+json.dumps({k:report[k] for k in ['verified_utc','archive_bytes','archive_sha256','base_verified_source_files','total_archive_files','passed']},ensure_ascii=False,indent=2)+'\nAll temporary junctions removed. Copy this entire folder.\n',encoding='utf-8')
with (OUT/'先读我.md').open('a',encoding='utf-8') as f:f.write('\n\n## 最终完成状态\n\n整包已完成逐文件 SHA-256 校验。最后的打包对话补档也已收入 ZIP 内 `conversation/latest-deltas`；详见其 index.json 的捕获截止时间。临时链接目录已清理，可以整目录复制。新电脑建议预留至少 20 GB 空间。\n')
print(json.dumps({k:report[k] for k in ['verified_utc','archive_bytes','archive_sha256','base_verified_source_files','total_archive_files','passed']},ensure_ascii=False),flush=True)
