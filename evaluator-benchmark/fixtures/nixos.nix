{ nixpkgs }:
let
  work = i: let
    s = import (nixpkgs + "/nixos/lib/eval-config.nix") {
      system = "x86_64-linux";
      modules = [{ pkgs, ... }: {
        system.stateVersion = "26.05";
        networking.hostName = "eval-${toString i}";
        boot.loader.grub.enable = false;
        fileSystems."/" = { device = "/dev/vda1"; fsType = "ext4"; };
        services.openssh.enable = true;
        services.nginx.enable = true;
        services.postgresql.enable = true;
        environment.systemPackages = [ pkgs.git pkgs.curl ];
      }];
    };
  in s.config.system.build.toplevel.drvPath;
in builtins.genList work 4
