# shell.nix
let
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/cf8cc1201be8bc71b7cbbbdaf349b22f4f99c7ae.tar.gz") {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
      pandas
      requests
      aiogram
    asyncpg
    alembic
    python-dotenv
    gspread 
    google-auth
    apscheduler
    pytz
    selenium
    ]))
  ];
}