{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/55bfb4d7437bd4e09ab7cba58a43bd68eb310044";
  outputs = { self, nixpkgs }: {
    bench = {
      language = import ./language.nix;
      shared = import ./shared.nix;
      packages = import ./packages.nix { inherit nixpkgs; };
      nixos = import ./nixos.nix { inherit nixpkgs; };
    };
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.hello;
  };
}
