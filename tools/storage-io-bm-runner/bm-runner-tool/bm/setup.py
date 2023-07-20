"""
Creates `fio` job files
"""
from bm.params import BenchmarkConfig, SWStackParam, StorageLevelParam, MeasurementTypeParam

import configparser
from dataclasses import dataclass
import enum



FIO_GLOBAL_LABEL = 'global'
IO_ENGINE_PSYNC = 'psync'

FIO_TRUE = 1
FIO_FALSE = 0
FIO_TEST_SIZE = '1G'

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



def generate_job(bmConfig: BenchmarkConfig, name, job_file):
    config = configparser.ConfigParser()

    io_engine_arg = None
    if bmConfig.sw_stack == SWStackParam.NATIVE:
        # TODO: is this correct?
        # io_engine_arg = IO_ENGINE_PSYNC
        True # (true by default?)
    elif bmConfig.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bmConfig.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bmConfig.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    elif bmConfig.sw_stack == SWStackParam.VIRTIO_BLK:
        # TODO
        assert False, 'not implemented'
    else:
        assert False, f"Not a valid benchmark config io sw stack: {bmConfig.sw_stack}"


    if bmConfig.encryption_switch:
        # TODO
        assert False, 'not implemented'

    if bmConfig.integrity_switch:
        # TODO
        assert False, 'not implemented'

    if bmConfig.storage_level == StorageLevelParam.FILE:
        True # no action required (true by default)
    elif bmConfig.storage_level == StorageLevelParam.BLOCK:
        # TODO
        assert False, 'not implemented'
    elif bmConfig.storage_level == StorageLevelParam.DATA:
        # TODO
        assert False, 'not implemented'
    else:
        assert False, f"Not a valid storage level: {bmConfig.storage_level}"

    # NOTE config based off of Spool (ATC'20) Table 2: FIO Test Cases
    # see https://github.com/TUM-DSE/CVM_eval/issues/9#issuecomment-1647670001


    fio_config = None
    if bmConfig.measurement_type == MeasurementTypeParam.BANDWIDTH:
        fio_config = BANDWIDTH_CONFIG
    elif bmConfig.measurement_type == MeasurementTypeParam.IOPS:
        fio_config = IOPS_CONFIG
    elif bmConfig.measurement_type == MeasurementTypeParam.AVG_LATENCY:
        fio_config = AVG_LATENCY_CONFIG
    else:
        assert False, f"Not a valid benchmark measurement type: {bmConfig.measurement_type}"

    # global config
    config[FIO_GLOBAL_LABEL] = {
            FioParamLabels.BLOCK_SIZE.value : f"{fio_config.block_size}K",
            FioParamLabels.IO_DEPTH.value   : fio_config.io_depth,
            FioParamLabels.NUM_JOBS.value   : fio_config.numjobs
            }

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

    # write result to job file
    with open(job_file, 'w') as jobfile:
        config.write(jobfile, space_around_delimiters=False)

