let
  work = seed: builtins.foldl' (a: b: a + b + seed) 0 (builtins.genList (x: x) 30000);
in builtins.genList (i: work i) 48
