## VM Netowrk Configuraiton

### NIC for ssh
- We use [QEMU user networking (SLIRP)](https://wiki.qemu.org/Documentation/Networking) for ssh.
- Guest configuration
    - IP address: 10.0.2.15
    - The configuration is `networking.interfaces.eth0` in the [guest-config.nix](../nix/guest-config.nix).
- The host can access to the guest via QEMU's port forwarding
    - `just ssh`
- QEMU command line is
```
    -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22
```

### virtio-nic
- This is for network evaluation
- The current scripts uses `virbr0` on the host
- Guest configuration
    - IP address: 172.44.0.2
    - The configuration is `networking.interfaces.eth1` in the [guest-config.nix](../nix/guest-config.nix).
- Host configuration
    - See `setup_bridge` in the [justfile](../justfile)
- Quick test
    - `ping 172.44.0.2` on the host
- QEMU command line is
```
    -netdev bridge,id=en0,br=virbr0
    -device virtio-net-pci,netdev=en0
```
