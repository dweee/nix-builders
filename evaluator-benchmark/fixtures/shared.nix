let
  common = builtins.genList (i: builtins.foldl' (a: b: a + b) i (builtins.genList (x: x) 2000)) 64;
  work = seed: builtins.foldl' (a: b: a + b + seed) 0 common;
in builtins.genList (i: work i) 128
