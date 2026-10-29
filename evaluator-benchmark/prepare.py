#!/usr/bin/env python3
"""Provision temporary release closures and record exact artifacts; no activation."""
import json, os, pathlib, platform, shutil, subprocess, sys
P=pathlib.Path(__file__).resolve().parent
system=('aarch64' if platform.machine() in ['arm64','aarch64'] else 'x86_64') + ('-darwin' if platform.system()=='Darwin' else '-linux')
state=pathlib.Path(sys.argv[1]).resolve(); state.mkdir(parents=True,exist_ok=True)
engines=[dict(name='installed',kind='nix',bin=shutil.which('nix'))]
urls={
 'cppnix-2.35.4':f'https://releases.nixos.org/nix/nix-2.35.4/nix-2.35.4-{system}.tar.xz',
 'determinate-3.24.1':f'https://install.determinate.systems/determinate-nix/tag/v3.24.1/{system}',
 'lix-2.95.4':f'https://releases.lix.systems/lix/lix-2.95.4/lix-2.95.4-{system}.tar.xz',
}
for name,url in urls.items():
    r=subprocess.check_output([sys.executable,str(P/'import-release.py'),url,str(state/name)],text=True)
    (state/(name+'.provenance.txt')).write_text(r)
    binary=next(line for line in r.splitlines() if line.startswith('/nix/store/'))+'/bin/nix'
    engines.append(dict(name=name,kind='nix',bin=binary,determinate=name.startswith('determinate')))
(state/'engines.json').write_text(json.dumps(engines,indent=2)+'\n')
print(state/'engines.json')
