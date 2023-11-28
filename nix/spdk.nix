{ pkgs }:

with pkgs;
spdk.overrideAttrs
(
  new: old:
  {
    # include setup.sh for spdk setup (e.g. hugepage allocation)
    # include nvme_manage for SSD preconditioning
    # as in: https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf
    postInstall =
    ''
      cp ./build/examples/nvme_manage $out/bin/.
      cp ./build/examples/perf $out/bin/.
      cp ./scripts/setup.sh $out/bin/spdk-setup.sh
      # setup dependencies
      mkdir -p $out/scripts
      cp ./scripts/common.sh $out/scripts/common.sh
      cp ./scripts/spdk-gpt.py $out/scripts/spdk-gpt.py
      cp ./scripts/rpc.py $out/bin/.
    '';
  }
)
