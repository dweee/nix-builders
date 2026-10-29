#!/usr/bin/env python3
"""Isolate lazy source materialization using a fresh 32 MiB local Git tree.

Commit creation and payload generation are outside the measured region. Each
cold trial gets its own revision and evaluator cache. A warm trial immediately
re-evaluates that exact revision. This does not evict OS page caches.
"""
import argparse, importlib.util, itertools, json, os, pathlib, random, shutil, subprocess, tempfile
P=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bench',P/'run.py');bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
a=argparse.ArgumentParser();a.add_argument('--engines',type=pathlib.Path,required=True);a.add_argument('--output',type=pathlib.Path,required=True);a.add_argument('--host',required=True);args=a.parse_args()
engines=json.loads(args.engines.read_text());e=next(e for e in engines if e.get('determinate'))
with tempfile.TemporaryDirectory(prefix='nix-source-trials-') as tmp:
 root=pathlib.Path(tmp);repo=root/'repo';repo.mkdir();conf=root/'conf';conf.mkdir()
 (repo/'flake.nix').write_text('{ outputs = { self }: { answer = builtins.fromJSON (builtins.readFile ./marker); }; }\n')
 (repo/'marker').write_text('42\n');payload=repo/'unused';payload.mkdir()
 rng=random.Random(29102026)
 for i in range(128): (payload/f'{i:03d}.bin').write_bytes(rng.randbytes(262144))
 def git(*cmd):
  return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Evaluator fixture','-c','user.email=fixture@example.invalid',*cmd],stderr=subprocess.DEVNULL,text=True).strip()
 git('init','-q');git('add','.')
 cases=list(itertools.product([1,0],[False,True],[False,True],range(3)));random.Random(29102026).shuffle(cases)
 for i,(cores,lazy,cache,rep) in enumerate(cases):
  (repo/'nonce').write_text(f'{i}\n');git('add','.');git('commit','-qm','Fixture revision');rev=git('rev-parse','HEAD')
  c=root/f'cache-{i}';c.mkdir()
  env=os.environ.copy();env.update(NIX_CONF_DIR=str(conf),NIX_USER_CONF_FILES='/dev/null',XDG_CACHE_HOME=str(c),NIX_CONFIG='experimental-features = nix-command flakes parallel-eval\nbuilders =\nmax-jobs = 0\n')
  opts={'eval-cores':cores,'lazy-trees':lazy,'eval-cache':cache}
  cmd=[e['bin'],'eval','--json','--no-write-lock-file']
  for k,v in opts.items(): cmd+=['--option',k,str(v).lower()]
  cmd += [f'git+file://{repo}?rev={rev}#answer']
  for mode in ['cold-source','warm-source']:
   r=bench.measure(cmd,env,120)
   row=dict(host=args.host,engine=e['name'],workload='source-32mib',mode=mode,options=opts,rep=rep,revision=rev,payload_bytes=33554432,command=cmd,**r)
   with args.output.open('a') as f:f.write(json.dumps(row)+'\n')
   print(args.host,mode,opts,r['returncode'],r['wall_s'],flush=True)
