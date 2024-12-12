{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  packages = [ pkgs.python312 pkgs.python312Packages.pip ];
  shellHook = ''
    ${pkgs.python312}/bin/python -m venv .venv
    source .venv/bin/activate
    make install
  '';
}
