# Attestation

## Linux
- Linux introduces "configs-tsm" to support a cross-vendor mechanism for getting
  attestation reports since Linux 6.7
    - [configfs-tsm commit](https://lore.kernel.org/lkml/654438f4ca604_3f6029413@dwillia2-mobl3.amr.corp.intel.com.notmuch/)
    - [SNP configfs support](https://github.com/torvalds/linux/commit/f47906782c76294b3468f7584f666bc114927aa1)
    - [TDX configfs support](https://github.com/torvalds/linux/commit/f4738f56d1dc62aaba69b33702a5ab098f1b8c63)
- With this, the guest can get an attestation report like the following (also see the above commits for the detail)
```
# the guest kernel should have CONFIG_CONFIGFS_FS
report=/sys/kernel/config/tsm/report/report0
mkdir $report

# check provider; for SNP, this shows "sev_guest", whereas "tdx_guest" for TDX
cat $report/provider

# check generation; this value is incremented after requesting a new report
cat $poret/generation

# write user data (64 bytes for both SNP and TDX) into inblob; this internally makes attestation request
dd if=/dev/urandom bs=64 count=1 > $report/inblob

# get an repport
cat $report/outblob > report.dat

# check generation again, this value should be incremented
cat $report/generation

# we can delete the directory after getting a report
rmdir $report
```
- Originally, SNP has `/dev/sev-guest` and TDX has `/dev/tdx-guest`. They
  defines each ioctl interface to get attestation reports. These interface
  seems lazily deprecated but are still available.
    - TDX also support getting a quote via vsock.
- I confirmed configfs-tsm works for SNP guest on the geust with Linux 6.8.
- I haven't confirmed for TDX guest yet. Seemingly we need to have DCAP v1.21
    - See: https://github.com/canonical/tdx/issues/111
- In practice, there are several tools that provides more high-level interface
  to users to get an attestation report (see below).
- Libraries
    - [google/go-configfs-tsm](https://github.com/google/go-configfs-tsm)

## AMD SEV-SNP
### Calculate guest launch measurement (on the host)
- We can calculate the guest launch measurement using [sev-snp-measure](https://github.com/virtee/sev-snp-measure)
```
% git clone https://github.com/virtee/sev-snp-measure
% cd sev-snp-measure
% nix run nixpkgs#python3 -- ./sev-snp-measure.py --mode snp --vcpus=4 --vcpu-type=EPYC-v4 --ovmf=../../CVM_eval/build/ovmf-amd-sev-snp-fd/FV/OVMF.fd
4af0aa02fe41302d34e508c1f1fff64e6364510360d70095d9582b0de384c20f24cc27bad6c9d0cd5f798d8b13b8e975
```

### Get attestation report (on the guest)
- We can use [snpguest](https://github.com/virtee/snpguest) to obtain an attestation report and certificates, and verify the report
- (July 2024) it seems snpguest still uses `/sev/sev-guest` interface, instead of configfs-tsm.
- Load sev-guest kernel module (if missing)
```
$ modprobe sev-guest
$ ls /dev/sev-guest
```
- get attestation report
```
$ git clone https://github.com/virtee/snpguest
$ cd snpguest
$ nix-shell -p cargo rustc
$ cargo build
# request attestation using random data
$ ./target/debug/snpguest report attestation-report.bin random-request-file.txt --random
# show attestation measurement
$ ./target/debug/snpguest display report attestation-report.bin
# -> measurement should match with the value calculated with the sev-snp-measure
[...]

Measurement:
4a f0 aa 02 fe 41 30 2d 34 e5 08 c1 f1 ff f6 4e
63 64 51 03 60 d7 00 95 d9 58 2b 0d e3 84 c2 0f
24 cc 27 ba d6 c9 d0 cd 5f 79 8d 8b 13 b8 e9 75

[...]
```

### Get certificates from AMD KDS
- We can also use snpguest to fetch certificates from AMD KDS
- Requests ARK, ASK from KDS
    - We can specify certificates format (pem or der)
```
$ ./target/debug/snpguest fetch ca der genoa ./certs-kds --endorser vcek
$ ls certs-kds/
ark.der  ask.der
```
- Requests VCEK
    - VCEK varies depending on TCB of bootloader, tee, snp, and microcode
    - [Get these information from the attestation report](https://github.com/virtee/snpguest/blob/0d77c10075c250c31219d8219b24eafcc428e2fb/src/fetch.rs#L242)
```
$ ./target/debug/snpguest fetch vcek der genoa ./certs-kds attestation-report.bin
$ ls certs-kds/
ark.der  ask.der  vcek.der
```

### Verify certificates and the report
- Verify certificates
```
$ ./target/debug/snpguest verify certs ./certs-kds/
The AMD ARK was self-signed!
The AMD ASK was signed by the AMD ARK!
The VCEK was signed by the AMD ASK!
```
- Verify the attestation report
```
$ ./target/debug/snpguest verify attestation ./certs-kds attestation-report.bin
Reported TCB Boot Loader from certificate matches the attestation report.
Reported TCB TEE from certificate matches the attestation report.
Reported TCB SNP from certificate matches the attestation report.
Reported TCB Microcode from certificate matches the attestation report.
Chip ID from certificate matches the attestation report.
VEK signed the Attestation Report!
```

### Extended guest request
- AMD KDS implements rate-limiting, therefore, using some caching mechanism
  is desirable especially for large cloud providers
    - Using the cache is totally fine, the guest can verify the certificates
- For that, SNP GHCB defines `SNP Extended Guest Requet`. This request is
  handled by the vmm (not ASP). If the VMM supports the request, then the vmm
  returns (cached) certificates, but the VMM is not required to support this feature
    - Note that in normal case, `snpguset fetch` fetches certificates via REST requests to the KDS
- We can use `snpguest certificates` command to get certificates using
  extended guest request ([snpguest's README](https://github.com/virtee/snpguest)
  explains this as "extended attestation flow")
```
$ ./target/debug/snpguest certificates pem ./certs
No certificates were loaded by the host...
```
- In this case, the host does not support extended guest request, returning no
  certificates
- TODO: how to support extended request with QEMU?

### VLEK
- SNP also supports VLEK.
- VLEK is for ensuring the VM is run on a specific cloud provider as VLEK is unique to the provider.
- [AWS example of VLEK](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/snp-attestation.html)

-----

## Intel TDX

### Preparation
- To perform attestation, we need to
    - have QGS (Quote Generation Service) on the host
    - have PCCS (cache service of certificates) on the host
        - Note that Intel requested us to use PCCS to avoid stressing PCS
    - register the platform (on the host)
- Check [the document of canonical/tdx](https://github.com/canonical/tdx?tab=readme-ov-file#8-setup-remote-attestation-on-host-os-and-inside-td)
- Container images for QGS and PCCS are also available
    - [cc-api/confidential-cloud-native-primitives/container](https://github.com/cc-api/confidential-cloud-native-primitives/tree/main/container)

### Get a report and quote
- [libtdx-attest-dev](https://github.com/intel/SGXDataCenterAttestationPrimitives/tree/main/QuoteGeneration/quote_wrapper/tdx_attest)
- These use configfs-tsm
    - [google/go-tdx-guest:tools/attest](https://github.com/google/go-tdx-guest/tree/main/tools/attest)
    - [cc-api/cc-trusted-vmsdk](https://github.com/cc-api/cc-trusted-vmsdk)

#### libtdx-attest-dev
- libtdx-attest is a library to get a report and a quote
    - Source is [here](https://github.com/intel/SGXDataCenterAttestationPrimitives/tree/main/QuoteGeneration/quote_wrapper/tdx_attest)
    - It supports config-tsm, vsock, and tdvmcall interface. Automatically
      fallbacking to other interface if the one is not available.
- `test_tdx_attest` is sample application that get a report and the quote
- On the Ubuntu guest
```
git clone https://github.com/canonical/tdx.git
cd tdx/attestation
./setup-attestation-guest.sh
cd /usr/share/doc/libtdx-attest-dev/examples/
./test_tdx_attest
# this saves report.bin and quote.dat if everything works fine
```

#### pytdxmeasure (deprecated)
- https://github.com/intel/tdx-tools/tree/tdx-1.5/attestation/pytdxmeasure
- On the guest
```
git clone https://github.com/intel/tdx-tools
cd tdx-tools
cd checkout -b tdx-1.5 origin/tdx-1.5
cd attestation/pytdxmeasure
./tdx_tdreport
```
- Now intel/tdx-tools repository is gone


### Quote Verification
- For verifying quotes, several tools available
    - [intel/SGXDataCenterAttestationPrimitives (QuoteVerificationSample)](https://github.com/intel/SGXDataCenterAttestationPrimitives/tree/main/SampleCode/QuoteVerificationSample)
    - [google/go-tdx-guest](https://github.com/google/go-tdx-guest)
    - [edgelesssys/go-tdx-qpl](https://github.com/edgelesssys/go-tdx-qpl)

#### SGXDataCenterAttestationPrimitives (QuoteVerificationSample)
- See [this](https://cc-enabling.trustedservices.intel.com/intel-tdx-enabling-guide/07/trust_domain_at_runtime/#td-quote-verification)
- (July 2024) The required dependencies are not available for Ubuntu 24.04 (noble) yet
- We can use docker to have Ubuntu mantic and compile the sample, but for some reason the attestation fails
    - docker command: `sudo docker run --name qv  -v $HOME/work:/share --net=host -it ubuntu:mantic`
        - after creating the docker image, `sudo docker start qv; sudo docker attach qv`
    - It seems some connection issues to PCCS. Maybe some docker network misconfiguration.
    - I haven't debugged this matter so much
```
# ./app -quote quote.dat
[APP] Info: ECDSA quote path: quote.dat
[APP] Quote verification with QVL, support both SGX and TDX quote:
[APP] Info: tee_get_quote_supplemental_data_version_and_size successfully returned.
[APP] Info: latest supplemental data major version: 3, minor version: 3, size: 536
[QCNL] Error:  Encountered CURL error: (60) SSL peer certificate or SSH remote key was not OK
[QPL] Error: Failed to get PCK CRL and certchain : 0xb033
[QPL] Error: Failed to get SGX quote verification collateral : 57445
[APP] Error: App: tee_verify_quote failed: 0xe065
```
- I copied "app" and libraries to the host and then it works
```
$ ls lib
libdcap_quoteprov.so.1           libsgx_dcap_quoteverify.so.1 libsgx_default_qcnl_wrapper.so.1
libdcap_quoteprov.so.1.13.108.3  libsgx_dcap_quoteverify.so.1.13.101.3 libsgx_default_qcnl_wrapper.so.1.13.108.3
$ LD_LIBRARY_PATH=./lib ./app -quote ./quote.dat
[APP] Info: ECDSA quote path: /home/sdp/work/attestation/go-tdx-guest/tools/check/quote.dat
[APP] Quote verification with QVL, support both SGX and TDX quote:
[APP] Info: tee_get_quote_supplemental_data_version_and_size successfully returned.
[APP] Info: latest supplemental data major version: 3, minor version: 3, size: 536
[APP] Info: App: tee_verify_quote successfully returned.
[APP] Info: App: Verification completed successfully.
[APP] Info: Supplemental data Major Version: 3
[APP] Info: Supplemental data Minor Version: 3
```

#### go-tdx-guest
```
git clone https://github.com/google/go-tdx-guest
cd go-tdx-guest-tools/check
go build check.go
./check -in quote.dat -collateral true
```
- `quote.dat` is the quote (obtain it using scp or something)
- Internally this fetches certificates, verify the certificates, and verify the quote
- By default this uses Intel PCS. [Change the URL](https://github.com/google/go-tdx-guest/blob/f2cf18e98537a20316b8c8d70907eddf4ef5c6be/pcs/pcs.go#L41-L42) to use local PCCS

### Trouble shooting

#### Failed to get quotes
- There would be several reasons but we should check the status of the services
```
# check QGSD
sudo systemctl status qgsd

# check platform registation
sudo systemctl status mpa_registration_tool
cat /var/log/mpa_registration.log
```

### Failed to verify quotes
- Check PCCS
```
# this should show REST logs
sudo systemctl status pccs

# manually access PCCS
curl -k -G "https://localhost:8081/sgx/certification/v4/qe/identity"
```
- Check the size of a quote
    - In my environment, the size is around 4.9K.
    - If the size is too small, then quote generation might have failed. Check
      the QGS service logs.
```
# ls -lh quote.dat
-rw-r--r-- 1 root root 4.9K Jul  8 18:09 quote.dat
```

#### PCCS returns "Internal server errors"
- e.g.,
```
$ curl -k -G "https://localhost:8081/sgx/certification/v4/qe/identity"
Internal server error occurred.
```
- This once happened when we reinstalling PCCS. At that time, recreating the
  cache db solved the issue
```
sudo su
cd /opt/intel/sgx-dcap-pccs
mv pckcache.db pckcache.db.bak
```
