"""
Creates `fio` job files
"""
from bm.params import BenchmarkConfig, SWStackParam, StorageLevelParam, \
    MeasurementTypeParam, ENCRYPTED_RAM_MAP_NAME, INTEGRITY_RAM_MAP_NAME, \
    ENCRYPTED_INTEGRITY_RAM_MAP_NAME

import configparser
from dataclasses import dataclass
import enum
import logging as log
import os
import subprocess


ENCRYPT_HDR_NAME = 'encrypthdr.img'
ENCRYPT_INTEGRITY_HDR_NAME = 'encrypt-integrity-hdr.img'
EXIT_SUCCESS = 0

FIO_GLOBAL_LABEL = 'global'
IO_ENGINE_PSYNC = 'psync'

FIO_TRUE = 1
FIO_FALSE = 0
FIO_TEST_SIZE = '4G'
FIO_LOOPS = 1

class FioParamLabels(str, enum.Enum):
    IO_ENGINE  = 'ioengine'
    IO_DEPTH   = 'iodepth'
    IO_TYPE    = 'rw'
    BLOCK_SIZE = 'bs'
    NUM_JOBS   = 'numjobs'
    DIRECT     = 'direct'
    SIZE       = 'size'
    MIXREAD    = 'rwmixread'
    MIXWRITE   = 'rwmixwrite'
    OUTPUT     = 'output'
    FILENAME   = 'filename'
    LOOPS      = 'loops'


class IOType(str, enum.Enum):
    READ = 'read'
    WRITE = 'write'
    RANDREAD = 'randread'
    RANDWRITE = 'randwrite'
    MIXREAD = 'mix-randread'
    MIXWRITE = 'mix-randwrite'


@dataclass
class FioTestConfig:
    # in K
    block_size: int
    io_type: [IOType]
    io_depth: int
    numjobs: int = 1
    # in %
    # only applied to MIXREAD / MIXWRITE, respectively
    rw_mixread: int = None
    rw_mixwrite: int = None


# pre-set FIO Test Configs
# NOTE config based off of Spool (ATC'20) Table 2: FIO Test Cases
# see https://github.com/TUM-DSE/CVM_eval/issues/9#issuecomment-1647670001
BANDWIDTH_CONFIG = FioTestConfig(128, [IOType.READ, IOType.WRITE], 128)
IOPS_CONFIG = FioTestConfig(
        4, [IOType.RANDREAD, IOType.MIXREAD, IOType.MIXWRITE, IOType.RANDWRITE],
        32, 4, 70, 30)
AVG_LATENCY_CONFIG = FioTestConfig(
        4, [IOType.RANDREAD, IOType.RANDWRITE, IOType.READ, IOType.WRITE], 1)



def generate_job(bm_config: BenchmarkConfig, name, job_file):
    config = configparser.ConfigParser()

    io_engine_arg = None
    if bm_config.sw_stack == SWStackParam.NATIVE:
        # TODO: is this correct?
        # io_engine_arg = IO_ENGINE_PSYNC
        True # (true by default?)
    elif bm_config.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bm_config.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bm_config.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bm_config.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    else:
        assert False, f"Not a valid benchmark config io sw stack: {bm_config.sw_stack}"


    if bm_config.storage_level == StorageLevelParam.FILE:
        # TODO - is fio on block or file level???
        True # no action required (true by default)
    elif bm_config.storage_level == StorageLevelParam.BLOCK:
        assert False, 'not implemented'
    elif bm_config.storage_level == StorageLevelParam.DATA:
        # TODO
        assert False, 'not implemented'
    else:
        assert False, f"Not a valid storage level: {bm_config.storage_level}"

    # NOTE config based off of Spool (ATC'20) Table 2: FIO Test Cases
    # see https://github.com/TUM-DSE/CVM_eval/issues/9#issuecomment-1647670001


    fio_config = None
    if bm_config.measurement_type == MeasurementTypeParam.BANDWIDTH:
        fio_config = BANDWIDTH_CONFIG
    elif bm_config.measurement_type == MeasurementTypeParam.IOPS:
        fio_config = IOPS_CONFIG
    elif bm_config.measurement_type == MeasurementTypeParam.AVG_LATENCY:
        fio_config = AVG_LATENCY_CONFIG
    else:
        assert False, f"Not a valid benchmark measurement type: {bm_config.measurement_type}"

    # global config
    config[FIO_GLOBAL_LABEL] = {
            FioParamLabels.BLOCK_SIZE.value : f"{fio_config.block_size}K",
            FioParamLabels.IO_DEPTH.value   : fio_config.io_depth,
            FioParamLabels.NUM_JOBS.value   : fio_config.numjobs,
            }
    
    # global config: file target ( enable encryption variants )
    if bm_config.encryption_switch and bm_config.integrity_switch:
        config[FIO_GLOBAL_LABEL][FioParamLabels.FILENAME.value] = f"{bm_config.encrypted_integrity_target_disk}"
    elif bm_config.encryption_switch:
        config[FIO_GLOBAL_LABEL][FioParamLabels.FILENAME.value] = f"{bm_config.encrypted_target_disk}"
    elif bm_config.integrity_switch:
        config[FIO_GLOBAL_LABEL][FioParamLabels.FILENAME.value] = f"{bm_config.integrity_target_disk}"
    else:
        config[FIO_GLOBAL_LABEL][FioParamLabels.FILENAME.value] = f"{bm_config.target_disk}"

    # per IO Type: separate job
    for io_type in fio_config.io_type:
        job_name = f"{name}-{io_type}"
        # special case: mix-r/w
        if io_type == IOType.MIXREAD:
            mixed_rw_entry = f'{fio_config.rw_mixread}%'
            # use RANDREAD / RANDWRITE label instead of MIX(R/W)
            # mapping to same label creates duplicate enums, causing this if-branch to branch
            # on RANDR/W as well - although we use the same label
            config[job_name] = { FioParamLabels.IO_TYPE.value : IOType.RANDREAD.value }
            config[job_name][FioParamLabels.MIXREAD.value] = f'{fio_config.rw_mixread}'
        elif io_type == IOType.MIXWRITE:
            config[job_name] = { FioParamLabels.IO_TYPE.value : IOType.RANDWRITE.value }
            config[job_name][FioParamLabels.MIXWRITE.value] = f'{fio_config.rw_mixwrite}'
        else:
            config[job_name] = { FioParamLabels.IO_TYPE.value : io_type.value }


    # global config independent of inputs

    # see https://github.com/TUM-DSE/CVM_eval/issues/9#issuecomment-1647732269
    config[FIO_GLOBAL_LABEL][FioParamLabels.DIRECT.value] = f"{FIO_TRUE}"
    # taken from ../../../fio.sh
    config[FIO_GLOBAL_LABEL][FioParamLabels.SIZE.value] = f"{FIO_TEST_SIZE}"
    config[FIO_GLOBAL_LABEL][FioParamLabels.FILENAME.value] = f"{bm_config.target_disk}"
    config[FIO_GLOBAL_LABEL][FioParamLabels.LOOPS.value] = f"{FIO_LOOPS}"

    # write result to job file
    with open(job_file, 'w') as jobfile:
        config.write(jobfile, space_around_delimiters=False)


def create_crypto_disk_hdr(hdr_path):
        # create disk encryption header if doesn't exist
        if not os.path.exists(hdr_path):
            subprocess.run(['fallocate', '-l', '2M', hdr_path]).check_returncode()


# from https://blog.cloudflare.com/speeding-up-linux-disk-encryption/
def setup_ramdisk(bm_config, resource_dir):
    # check if ramdisk exists, if not, create it

    if not os.path.exists(bm_config.target_disk):
        log.warn(f"No RAMDisk found at {bm_config.target_disk}; " \
                "creating 4G RAMDisk. Requires `sudo`.")
        # TODO annotate / replace literals
        # changing target_disk path requires changing rd_nr
        subprocess.run(['sudo', 'modprobe', 'brd', 'rd_nr=1', 'rd_size=4194304']).check_returncode()

    if bm_config.encryption_switch:
        # enrypted map already exists: skip setup
        if (not os.path.exists(bm_config.encrypted_target_disk) and not bm_config.integrity_switch) \
            or (not os.path.exists(bm_config.integrity_target_disk) and bm_config.integrity_switch):
            log.warn(f"Attempting to encrypt {bm_config.target_disk}; " \
                    "requires `sudo` and user interaction.")

            cryptsetup_cmd = ['sudo', 'cryptsetup', 'luksFormat',
                  bm_config.target_disk, '--perf-no_read_workqueue',
                  '--perf-no_write_workqueue']
            # if integrity on top of encryption
            # from https://gist.github.com/MawKKe/caa2bbf7edcc072129d73b61ae7815fb
            selected_hdr = None
            selected_name = None
            if bm_config.integrity_switch:
                cryptsetup_cmd.append('--integrity')
                cryptsetup_cmd.append('hmac-sha256')
                selected_hdr = os.path.join(resource_dir, ENCRYPTED_INTEGRITY_RAM_MAP_NAME)
                selected_name = ENCRYPTED_INTEGRITY_RAM_MAP_NAME
            else:
                selected_hdr = os.path.join(resource_dir, ENCRYPT_HDR_NAME)
                selected_name = ENCRYPTED_RAM_MAP_NAME

            cryptsetup_cmd.append('--header')
            cryptsetup_cmd.append(selected_hdr)
            create_crypto_disk_hdr(selected_hdr)

            # disable read / writequeue
            # https://blog.cloudflare.com/speeding-up-linux-disk-encryption/
            subprocess.run(cryptsetup_cmd).check_returncode()
            
            # unlock ramdisk
            subprocess.run(['sudo', 'cryptsetup', 'open',
                '--header', selected_hdr, bm_config.target_disk, selected_name]).check_returncode()
    # only integrity
    elif bm_config.integrity_switch:
        # from https://gist.github.com/MawKKe/caa2bbf7edcc072129d73b61ae7815fb
        # integrity map already exists
        if not os.path.exists(bm_config.integrity_target_disk):
            log.warn(f"Attempting to integrity protect {bm_config.target_disk}; " \
                    "requires `sudo` and user interaction.")
            subprocess.run(['sudo', 'integritysetup', 'format', '--integrity',
                'sha256', bm_config.target_disk]).check_returncode()
            subprocess.run(['sudo', 'integritysetup', 'open', '--integrity',
                'sha256', bm_config.target_disk, INTEGRITY_RAM_MAP_NAME]).check_returncode()


