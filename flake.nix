{
  description = "dev env for cards";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-25.05";

    # NOTE that doesnt work for me, some build problem
    # maybe https://github.com/boisgera/pandoc will update it, currently it doesnt seem too broken (?)
    # the python package https://boisgera.github.io/pandoc/
    # currently wants pandoc at version 3.2.1
    # see https://lazamar.co.uk/nix-versions/?package=pandoc
    # pandocpkgs.url = "github:nixos/nixpkgs?rev=efcb904a6c674d1d3717b06b89b54d65104d4ea7";
    # and then use pandocpkgs.legacyPackages.${system}.haskellPackages.pandoc_3_2_1
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
        # also ad sudo apt install texlive texlive-full ?
        # npm install -g katex worked? nodePackages_latest.katex brakes node stuff with basedpyright
        # TODO there is also pandoc-katex ?
        # TODO an overlay would be better than using pandocpkgs directly? in case something else installs it too?
        paths = [ python uv ] ++ (with pkgs; [ ruff basedpyright pandoc ]);
        extraOutputsToInstall = [ "lib" ];
      };
    in
    {
      packages.${system} = {
        default = dev;
      };
    };
}
