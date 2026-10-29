#!/usr/bin/env python3
"""Import an official Nix/Lix release closure without installing or activating it."""
import hashlib, json, os, pathlib, struct, subprocess, sys, tarfile, tempfile, urllib.request
url, destination = sys.argv[1:3]
dest = pathlib.Path(destination)
dest.mkdir(parents=True, exist_ok=True)
archive = dest / 'release.tar.xz'
if not archive.exists():
    urllib.request.urlretrieve(url, archive)
print(json.dumps({'url': url, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}), flush=True)
with tarfile.open(archive) as t:
    for member in t.getmembers():
        if member.name.startswith('/') or '..' in pathlib.PurePosixPath(member.name).parts:
            raise ValueError('Unsafe archive path')
        if member.issym() and member.linkname.startswith('/') and not member.linkname.startswith('/nix/store/'):
            raise ValueError('Unexpected absolute symlink')
    t.extractall(dest, filter='fully_trusted')
reg = next(dest.glob('*/.reginfo'))
lines = iter(reg.read_text().splitlines())
records = {}
for path in lines:
    narhash, size, deriver, count = next(lines), next(lines), next(lines), int(next(lines))
    records[path] = (narhash, deriver, [next(lines) for _ in range(count)])
ordered, seen = [], set()
def visit(path):
    if path in seen: return
    seen.add(path)
    for ref in records[path][2]:
        if ref != path and ref in records: visit(ref)
    ordered.append(path)
for path in records: visit(path)
def number(n): return struct.pack('<Q', n)
def string(s):
    b = s.encode()
    return number(len(b)) + b + b'\0' * (-len(b) % 8)
with tempfile.TemporaryFile() as export:
    for path in ordered:
        if subprocess.run(['nix-store', '--check-validity', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0: continue
        narhash, deriver, refs = records[path]
        with tempfile.NamedTemporaryFile() as nar:
            subprocess.run(['nix-store', '--dump', str(reg.parent / 'store' / pathlib.Path(path).name)], stdout=nar, check=True)
            actual = subprocess.check_output(['nix-hash', '--type', 'sha256', '--base32', '--flat', nar.name], text=True).strip()
            if narhash != 'sha256:' + actual: raise ValueError('NAR hash mismatch: ' + path)
            export.write(number(1)); nar.seek(0)
            import shutil
            shutil.copyfileobj(nar, export)
        export.write(number(0x4558494e) + string(path) + number(len(refs)))
        for ref in refs: export.write(string(ref))
        export.write(string(deriver) + number(0))
    export.write(number(0)); export.seek(0)
    subprocess.run(['nix-store', '--import'], stdin=export, stdout=subprocess.DEVNULL, check=True)
for path in records:
    if (pathlib.Path(path) / 'bin/nix').exists(): print(path, flush=True)
