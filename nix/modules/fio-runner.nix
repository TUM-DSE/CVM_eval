{
  pkgs
  , config
  , encrypted-run ? false
  , ...
}:
{
  # execute upon start up
  # TODO: parameterize w/ io_uring
  # TODO: change for polling ; creates log file right away, not only after completion
  # issue for polling
  systemd.services.fio-runner =
  {
    description = "execute fio benchmark";
    script =
    ''
      /run/current-system/sw/bin/fio /mnt/blk-bm.fio \
        --output=/mnt/bm-result.log ${if encrypted-run then "--filename=/dev/mapper/crypt-target" else ""}
    '';
    wantedBy = [ "multi-user.target" ]; # starts after login
  };

}
