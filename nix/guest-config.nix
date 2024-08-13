# common nixos guest configuration

{ extraEnvPackages ? [ ], _gcc }:

{ pkgs, lib, modulesPath, ... }:

let
  keys = map (key: "${builtins.getEnv "HOME"}/.ssh/${key}") [
    "id_rsa.pub"
    "id_ecdsa.pub"
    "id_ed25519.pub"
  ];
  test-dmcrypt = pkgs.writeScriptBin "test-dmcrypt" ''
    #!/usr/bin/env bash
    set -u
    yes "" | ${pkgs.cryptsetup}/bin/cryptsetup luksOpen /dev/vda target
    echo "hello" > /dev/mapper/target
  '';
  outb = pkgs.callPackage ./bin/outb.nix { inherit pkgs; };
  pts = pkgs.phoronix-test-suite.override { gcc = _gcc; };
in
{
  imports = [ (modulesPath + "/profiles/qemu-guest.nix") ];

  nix.extraOptions =
    ''
      experimental-features = nix-command flakes
      keep-outputs = true
      keep-derivations = true
      auto-optimise-store = false
    '';
  nix.package = pkgs.nixFlakes;
  nix.gc.automatic = false;

  # virtio-console login setting
  # (somehow udev does not pick up hvc0?)
  systemd.services."serial-getty" = {
    wantedBy = [ "multi-user.target" ];
    serviceConfig.ExecStart = "${pkgs.util-linux}/sbin/agetty  --login-program ${pkgs.shadow}/bin/login --autologin root hvc0 --keep-baud vt100";
  };
  systemd.services."serial-getty@hvc0".enable = false;

  # boot time logging
  systemd.services."boottime-log" = {
    description = "Log boot time";
    wantedBy = [ "multi-user.target" ];
    # idle service is executed after all other active jobs are dispatched
    serviceConfig.Type = "idle";
    serviceConfig.ExecStart = "${outb}/bin/outb";
    enable = true;
  };

  # XXX: this systemd-networkd configuration seems not work, why?
  # systemd.network.enable = true;
  # # qemu network (for ssh)
  # systemd.network.networks."10-eth0" = {
  #   matchConfig.Name = "eth0";
  #   address = [ "10.0.2.15/24" ];
  #   routes = [
  #     { routeConfig.Gateway = "10.0.2.2"; }
  #   ];
  #   networkConfig.DHCP = "no";
  #   linkConfig.RequiredForOnline = "routable";
  # };
  # # virtio-net
  # systemd.network.networks."20-eth1" = {
  #   matchConfig.Name = "eth1";
  #   address = [ "172.44.0.2/24" ];
  #   networkConfig.DHCP = "no";
  # };
  # services.resolved.enable = false;
  # networking.useNetworkd = true;

  networking.networkmanager.enable = true;
  networking.interfaces.eth0.ipv4.addresses = [{
    address = "10.0.2.15";
    prefixLength = 24;
  }];
  networking.interfaces.eth1.ipv4.addresses = [
    {
      address = "172.45.0.2";
      prefixLength = 24;
    }
    {
      address = "192.168.100.11";
      prefixLength = 24;
    }
  ];
  networking.useDHCP = false;
  networking.interfaces.eth0.useDHCP = false;
  networking.interfaces.eth1.useDHCP = false;
  networking.defaultGateway = "10.0.2.2";
  networking.nameservers = [ "10.0.2.3" ];
  networking.firewall.enable = false;

  # don't wait for network to be online
  systemd.services.systemd-networkd-wait-online.enable = false;
  systemd.services.NetworkManager-wait-online.enable = false;
  systemd.network.wait-online.enable = false;
  systemd.network.wait-online.anyInterface = false;

  # no auto-updates
  systemd.services.update-prefetch.enable = false;

  # override defaults from nixpkgs/modules/virtualization/container-config.nix
  # to enable cryptsetup
  services.udev.enable = lib.mkForce true;
  services.lvm.enable = lib.mkForce true;

  # login with empty password
  users.extraUsers.root.initialHashedPassword = "";
  services.openssh.enable = true;

  users.users.root.openssh.authorizedKeys.keyFiles =
    lib.filter builtins.pathExists keys;

  time.timeZone = "Europe/Berlin";
  i18n.defaultLocale = "en_US.UTF-8";
  system.stateVersion = "23.11";

  # host-file sharing
  fileSystems."/share" = {
    device = "share";
    fsType = "9p";
    options = [ "trans=virtio" "nofail" "msize=104857600" ];
  };

  users.users.root.openssh.authorizedKeys.keys =
    [ (builtins.readFile ./ssh_key.pub) ];

  services.getty.helpLine = ''
    Log in as "root" with an empty password.
    If you are connect via serial console:
    Type Ctrl-a c to switch to the qemu console
    and `quit` to stop the VM.
  '';

  services.getty.autologinUser = lib.mkDefault "root";

  documentation.doc.enable = false;
  documentation.man.enable = false;
  documentation.nixos.enable = false;
  documentation.info.enable = false;
  programs.bash.enableCompletion = false;
  programs.command-not-found.enable = false;

  environment.systemPackages = with pkgs; [
    devmem2
    bpftrace
    tmux
    vim
    git
    fio
    iperf
    just
    psmisc # killall
    cryptsetup
    lvm2
    jq
    sysstat # mpstat, iostat, sar

    # phoronix test suite and dependencies to install tests
    #phoronix-test-suite
    pts
    # pts/memory
    unzip
    # pts/sysbench
    libaio
    libtool
    autoconf
    automake
    pkg-config
    # pts/npb => use OpenMPI version of NPB
    _gcc
    gfortran13
    gnumake
    mpi
    bc
    # pts/compression
    cmake
    p7zip
    ## pts/llm => requires ~100GB disk
    ## blas
    ## pts/build-linux-kernel => requires FHS env
    ## bc
    ## bison
    ## flex
    ## openssl

    # custom tools
    outb
    test-dmcrypt
  ] ++ extraEnvPackages;

  # additonal kernel parameters
  # boot.kernelParams = [ ];

  boot.loader.grub.enable = false;
  boot.initrd.enable = false;
  boot.isContainer = true;
  boot.loader.initScript.enable = true;
}
