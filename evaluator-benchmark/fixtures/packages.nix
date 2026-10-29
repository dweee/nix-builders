{ nixpkgs }:
let
  pkgs = import nixpkgs { system = "x86_64-linux"; config = {}; overlays = []; };
  names = [ "hello" "git" "curl" "wget" "bash" "coreutils" "findutils" "gnugrep" "gnused" "gawk" "jq" "ripgrep" "fd" "bat" "fzf" "tmux" "neovim" "vim" "emacs" "python3" "nodejs" "go" "rustc" "cargo" "gcc" "clang" "llvm" "cmake" "ninja" "meson" "pkg-config" "openssl" "zlib" "xz" "zstd" "sqlite" "postgresql" "redis" "nginx" "caddy" "systemd" "nix" "lix" "nixfmt" "alejandra" "nil" "nixd" "shellcheck" "shfmt" "ruff" "gnumake" "gdb" "strace" "ltrace" "htop" "btop" "ncdu" "duf" "tree" "rsync" "rclone" "restic" "borgbackup" "openssh" "tailscale" "wireguard-tools" "util-linux" "e2fsprogs" "btrfs-progs" "dosfstools" "parted" "lvm2" "cryptsetup" "smartmontools" "pciutils" "usbutils" "iproute2" "iptables" "nftables" "tcpdump" ];
in builtins.map (name: { inherit name; version = pkgs.${name}.version or "unknown"; drv = pkgs.${name}.drvPath; }) names
