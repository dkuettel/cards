{
  description = "dev env for cards";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-25.05";
  };

  outputs = { self, nixpkgs, ... }@inputs:
    let
      inherit (nixpkgs) lib;
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python313;
      uv = pkgs.writeScriptBin "uv" ''
        #!${pkgs.zsh}/bin/zsh
        set -eu -o pipefail
        UV_PYTHON=${python}/bin/python ${pkgs.uv}/bin/uv --no-python-downloads $@
      '';
      dev = pkgs.buildEnv {
        name = "dev";
        # sudo apt install pandoc texlive texlive-full ?
        # npm install -g katex worked?
        # TODO there is also pandoc-katex ?
        paths = [ python uv ] ++ (with pkgs; [ ruff basedpyright pandoc nodePackages_latest.katex ]);
        extraOutputsToInstall = [ "lib" ];
      };
    in
    {
      packages.${system} = {
        default = dev;
      };
    };
}
