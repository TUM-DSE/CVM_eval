{
  pkgs
  , config
  , lib
  , ...
}:
{
  options = with lib;
  {
    programs.fio-runner.enable = mkOption
    {
      type = types.bool;
      description =
      ''
        If fio should run upon starting VM
      '';
      default = false;
    };
    programs.fio-runner.encrypted-run = mkOption
    {
      type = types.bool;
      description =
      ''
        If fio should write to encrypted disk map
      '';
      default = false;
    };
    programs.fio-runner.bounce-buffer = mkOption
    {   
      type = types.bool;
      description =
      ''
        If the benchmark should use the bounce buffer (swiotlb)
      '';
      default = false;
    };
  };
  # execute upon start up
  # TODO: parameterize w/ io_uring
  # TODO: change for polling ; creates log file right away, not only after completion
  # issue for polling

  config = lib.mkIf config.programs.fio-runner.enable
  {
    systemd.services.fio-runner =
    {
      description = "execute fio benchmark";
      script =
      ''
        /run/current-system/sw/bin/fio /mnt/blk-bm.fio \
          --output=/mnt/bm-result.log ${if config.programs.fio-runner.encrypted-run then "--filename=/dev/mapper/crypt-target" else ""}
      '';
      wantedBy = [ "multi-user.target" ]; # starts after login
    };
    # for bounce buffer test
    boot.kernelParams = lib.mkIf config.programs.fio-runner.bounce-buffer [ "swiotlb=force" ];
  };
}
