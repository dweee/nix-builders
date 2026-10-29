#!/usr/bin/env python3
"""Fleet evaluator study. No builds, IFD, activation, or system cache eviction."""
import argparse, datetime, hashlib, itertools, json, os, pathlib, platform, random, resource, shutil, signal, subprocess, tempfile, threading, time
P = pathlib.Path(__file__).resolve().parent

def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def measure(cmd, env, timeout, rust=False):
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        start = time.perf_counter()
        p = subprocess.Popen(cmd, env=env, stdout=out, stderr=err, start_new_session=True)
        timedout = []
        def kill():
            timedout.append(True)
            try: os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        timer = threading.Timer(timeout, kill); timer.start()
        _, status, usage = os.wait4(p.pid, 0)
        elapsed = time.perf_counter() - start
        timer.cancel(); p.returncode = os.waitstatus_to_exitcode(status)
        out.seek(0); err.seek(0)
        stdout, stderr = out.read(), err.read().decode(errors='replace')
    result = dict(wall_s=elapsed, user_s=usage.ru_utime, sys_s=usage.ru_stime,
                  rss_mib=usage.ru_maxrss / (1048576 if platform.system() == 'Darwin' else 1024),
                  returncode=p.returncode, timeout=bool(timedout), stderr=stderr[-6000:])
    if not p.returncode:
        try:
            value = json.loads(stdout)
            if rust: value = json.loads(value)
            # Rust evaluators render builtins.toJSON as a Nix string.
            result['digest'] = canonical(value)
        except Exception as e:
            result['parse_error'] = str(e); result['stdout'] = stdout[-1000:].decode(errors='replace')
    return result

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--engines', required=True, type=pathlib.Path)
    a.add_argument('--output', required=True, type=pathlib.Path)
    a.add_argument('--host', default=platform.node())
    a.add_argument('--repetitions', type=int, default=3)
    a.add_argument('--timeout', type=int, default=180)
    a.add_argument('--quick', action='store_true')
    a.add_argument('--workloads', nargs='+')
    args = a.parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    engines = json.loads(args.engines.read_text())
    fixtures = P / 'fixtures'
    meta = json.loads(subprocess.check_output(['nix', '--extra-experimental-features', 'nix-command flakes', 'flake', 'metadata', 'path:' + str(fixtures), '--json']))
    np = json.loads(subprocess.check_output(['nix', '--extra-experimental-features', 'nix-command flakes', 'flake', 'archive', 'github:NixOS/nixpkgs/55bfb4d7437bd4e09ab7cba58a43bd68eb310044', '--json']))['path']
    base = args.output.parent / ('cache-' + args.host)
    base.mkdir(parents=True, exist_ok=True)
    conf = base / 'empty-conf'; conf.mkdir(exist_ok=True)
    rows = []
    for e in engines:
        e['version'] = e.get('revision') or subprocess.check_output([e['bin'], '--version'], text=True, stderr=subprocess.STDOUT).strip()
        if e['kind'] == 'nix':
            r = subprocess.run([e['bin'], '--extra-experimental-features', 'nix-command flakes', 'config', 'show', '--json'], text=True, capture_output=True)
            if r.returncode: r = subprocess.run([e['bin'], '--extra-experimental-features', 'nix-command flakes', 'show-config', '--json'], text=True, capture_output=True)
            allowed = ['eval-cores','eval-max-fibers','lazy-trees','eval-cache','experimental-features','cores','max-jobs']
            e['settings'] = {k:v for k,v in json.loads(r.stdout).items() if k in allowed} if r.returncode == 0 else {'error':r.stderr[-1000:]}
        jobs = []
        if e['kind'] == 'nix':
            jobs += [(w, {'eval-cache':False}, 'direct') for w in ['language','shared','packages','nixos']]
            jobs += [('cache-scalar', {'eval-cache':True}, state) for state in ['cold','warm']]
        else:
            jobs += [(w, {}, 'direct') for w in ['language','shared','packages','nixos']]
        if e.get('determinate'):
            # Factorial of source handling, cache and worker count. Cache=true JSON
            # still forces the full nested value; scalar cache is tested separately.
            cores = list(dict.fromkeys([1,2,4] + ([8] if os.cpu_count() >= 8 else []) + [0]))
            for c, lazy, cache in itertools.product(cores, [False,True], [False,True]):
                for w in ['packages','nixos']:
                    jobs.append((w, {'eval-cores':c,'lazy-trees':lazy,'eval-cache':cache,'eval-max-fibers':0}, 'flake'))
            # Fiber pressure and explicit parallel primitive: focused all-core sweep.
            for fibers, lazy in itertools.product([1, max(1,os.cpu_count()), 16*os.cpu_count()], [False, True]):
                jobs.append(('nixos', {'eval-cores':0,'lazy-trees':lazy,'eval-cache':False,'eval-max-fibers':fibers}, 'flake'))
            for c in cores:
                for w in ['language','shared','nixos']:
                    jobs.append((w, {'eval-cores':c,'eval-cache':False}, 'explicit-parallel'))
            for lazy, cache in itertools.product([False,True], [False,True]):
                jobs += [('cache-scalar',{'lazy-trees':lazy,'eval-cache':cache,'eval-cores':0},state) for state in ['cold','warm']]
        if args.quick: jobs = jobs[:4]
        if args.workloads: jobs = [job for job in jobs if job[0] in args.workloads]
        random.Random(29102026).shuffle(jobs)
        for w, options, mode in jobs:
            key = canonical([e['name'],w,options,mode])[:16]
            cache = base / key; cache.mkdir(exist_ok=True)
            env = os.environ.copy()
            for k in ['NIX_CONFIG','NIX_PATH','NIX_SHOW_STATS','NIX_COUNT_CALLS','GC_INITIAL_HEAP_SIZE','GC_DONT_GC']:
                env.pop(k, None)
            env.update(NIX_CONF_DIR=str(conf), NIX_USER_CONF_FILES='/dev/null', XDG_CACHE_HOME=str(cache),
                       NIX_CONFIG='experimental-features = nix-command flakes\nbuilders =\nmax-jobs = 0\nallow-import-from-derivation = false\nwarn-dirty = false\n')
            if e.get('determinate'):
                env['NIX_CONFIG'] += 'extra-experimental-features = parallel-eval\n'
            if e['kind'] == 'nix':
                cmd = [e['bin'], 'eval', '--offline', '--json', '--no-write-lock-file']
                for k,v in options.items(): cmd += ['--option',k,str(v).lower()]
                if mode in ['flake','cold','warm']:
                    attr = 'packages.x86_64-linux.default.drvPath' if w == 'cache-scalar' else 'bench.'+w
                    cmd += ['path:' + str(fixtures) + '#' + attr]
                else:
                    expr = 'import ' + str(fixtures / (w+'.nix'))
                    if w in ['packages','nixos']: expr += ' { nixpkgs = ' + np + '; }'
                    if mode == 'explicit-parallel': expr = 'let values = (' + expr + '); in builtins.parallel values values'
                    cmd += ['--impure','--expr',expr]
            else:
                expr = 'import ' + str(fixtures / (w+'.nix'))
                if w in ['packages','nixos']: expr += ' { nixpkgs = ' + np + '; }'
                cmd = [e['bin'], '--raw', '--expr', 'builtins.toJSON (' + expr + ')']
            print(args.host,e['name'],w,mode,options,flush=True)
            warmup = None
            if mode != 'cold': warmup = measure(cmd,env,args.timeout,e['kind'] != 'nix')
            # A failed warmup is evidence, not a speed result; do not repeat it.
            for rep in range(args.repetitions if not warmup or warmup.get('digest') else 1):
                if mode == 'cold':
                    shutil.rmtree(cache); cache.mkdir()
                r = measure(cmd,env,args.timeout,e['kind'] != 'nix')
                row = dict(host=args.host,engine=e['name'],version=e['version'],workload=w,mode=mode,options=options,rep=rep,command=cmd,**r)
                rows.append(row)
                with args.output.open('a') as f: f.write(json.dumps(row)+'\n')
                if r['returncode'] or 'digest' not in r: break
    unexpected = [r for r in rows if r['workload'] == 'language' and (r['returncode'] or 'digest' not in r)]
    manifest = dict(host=args.host,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),platform=platform.platform(),machine=platform.machine(),cpus=os.cpu_count(),load=os.getloadavg(),engines=engines,nixpkgs=np,fixture_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures.iterdir() if p.is_file()},repetitions=args.repetitions)
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if unexpected: raise SystemExit('Language validation failed; inspect raw trial errors')

if __name__ == '__main__': main()
