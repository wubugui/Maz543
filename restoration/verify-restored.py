"""Verify the restored snapshot against its source SHA-256 manifest before edits."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path(r'E:\COPY_THIS_FOLDER\MAZ543_COMPLETE_20260906.zip')

def check(row):
    path = ROOT / row['path']
    if not path.is_file():
        return {'path': row['path'], 'error': 'missing'}
    if path.stat().st_size != row['size']:
        return {'path': row['path'], 'error': 'size mismatch'}
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != row['sha256']:
        return {'path': row['path'], 'error': 'sha256 mismatch'}

if __name__ == '__main__':
    started = time.time()
    with zipfile.ZipFile(ARCHIVE) as archive:
        rows = json.loads(archive.read('migration/MANIFEST.json'))
        indexed = {row['path'] for row in rows}
        # Final conversation deltas and manifest itself were appended after inventory.
        for member in archive.infolist():
            if not member.is_dir() and member.filename not in indexed:
                with archive.open(member) as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                rows.append({'path': member.filename, 'size': member.file_size, 'sha256': digest})
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for count, failure in enumerate(pool.map(check, rows), 1):
            if failure:
                failures.append(failure)
            if count % 25000 == 0:
                print(f'Checked {count}/{len(rows)}; failures={len(failures)}', flush=True)
    report = {'archive': str(ARCHIVE), 'workspace': str(ROOT), 'verifiedFiles': len(rows),
              'verifiedBytes': sum(row['size'] for row in rows), 'failures': failures,
              'passed': not failures, 'elapsedSeconds': round(time.time() - started, 2)}
    (ROOT / 'restoration/snapshot-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)
    raise SystemExit(bool(failures))
