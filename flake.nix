{
  description = "dev env for cards";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-25.05";

    # the python package https://boisgera.github.io/pandoc/ currently needs pandoc 3.2.1 or lower
    # was trying with https://lazamar.co.uk/nix-versions/?package=pandoc but it's somehow totally off
    # nixos-25.05 has 3.6
    pandocpkgs.url = "github:nixos/nixpkgs?rev=3e2cf88148e732abc1d259286123e06a9d8c964a";  # 3.1.11.1
  };

  outputs = { self, nixpkgs, pandocpkgs, ... }@inputs:
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
        # also ad sudo apt install texlive texlive-full ?
        # npm install -g katex worked? nodePackages_latest.katex brakes node stuff with basedpyright
        # TODO there is also pandoc-katex ?
        paths = [ python uv ] ++ (with pkgs; [ ruff basedpyright pandocpkgs.legacyPackages.${system}.pandoc ]);
        extraOutputsToInstall = [ "lib" ];
      };
    in
    {
      packages.${system} = {
        default = dev;
      };
    };
}
