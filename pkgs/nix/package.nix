{
  lib,
  pkgs,
  pythonSet,
  pyproject-nix,
  workspace,
  ...
}: let
  inherit (pkgs.callPackage pyproject-nix.build.util {}) mkApplication;
in {
  default = mkApplication {
    venv = pythonSet.mkVirtualEnv "application-env" workspace.deps.default;
    package = pythonSet.textual-gittui;
    meta = {
      description = "A git tui built with textual";
      homepage = "https://github.com/TotalyEnglizLitrate/textual-gittui";
      maintainers = with lib.maintainers; [TotalyEnglizLitrate];
    };
  };
}
