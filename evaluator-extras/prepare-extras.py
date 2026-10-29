#!/usr/bin/env python3
"""Add current Lix and the pinned CppNix development snapshot."""
import json,pathlib,platform,subprocess,sys
P=pathlib.Path(__file__).resolve().parent
state=pathlib.Path(sys.argv[1]).resolve();state.mkdir(parents=True,exist_ok=True)
system=('aarch64' if platform.machine() in ['arm64','aarch64'] else 'x86_64') + ('-darwin' if platform.system()=='Darwin' else '-linux')
r=subprocess.check_output([sys.executable,str(P/'import-release.py'),f'https://releases.lix.systems/lix/lix-2.96.0/lix-2.96.0-{system}.tar.xz',str(state/'lix-2.96.0')],text=True)
(state/'lix-2.96.0.provenance.txt').write_text(r)
engines=[dict(name='lix-2.96.0',kind='nix',bin=next(l for l in r.splitlines() if l.startswith('/nix/store/'))+'/bin/nix')]
np=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes','flake','archive','github:NixOS/nixpkgs/55bfb4d7437bd4e09ab7cba58a43bd68eb310044','--json']))['path']
expr='(import '+np+' { config = {}; overlays = []; }).nixVersions.git'
p=subprocess.run(['nix','--extra-experimental-features','nix-command flakes','build','--impure','--no-link','--print-out-paths','--max-jobs','0','--builders','','--option','substituters','https://cache.nixos.org','--expr',expr],text=True,capture_output=True)
(state/'cppnix-pre.provenance.txt').write_text(p.stdout+p.stderr)
if p.returncode == 0:
    engines.append(dict(name='cppnix-2.36pre20261013',kind='nix',bin=p.stdout.strip().splitlines()[-1]+'/bin/nix'))
(state/'extras.json').write_text(json.dumps(engines,indent=2)+'\n')
