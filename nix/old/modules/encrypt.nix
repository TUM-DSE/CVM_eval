{
  pkgs
  , config
  , ...
}:
{
  boot.initrd.luks.devices."crypt-target" =
  {
    device = "/dev/vdb";
    tryEmptyPassphrase = true;
    keyFileSize = 256;
  };
}
