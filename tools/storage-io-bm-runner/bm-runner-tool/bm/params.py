import enum


# param enum types
## P3: Storage IO Software Stack
class SWStackParam(str, enum.Enum):
    NATIVE      = 'native-io'
    VIRTIO_BLK  = 'virtio-blk'
    VIRTIO_NVME = 'virtio-nvme'
    VIRTIO_SCSI = 'virtio-scsi'

## P5: Storage Level
class StorageLevelParam(str, enum.Enum):
    BLOCK = 'block-level'
    FILE  = 'file-level'
    DATA  = 'data-level'

## P6: Measurement Type
class MeasurementTypeParam(str, enum.Enum):
    IOPS        = 'iops'
    AVG_LATENCY = 'io-average-latency'
    BANDWIDTH   = 'io-bandwidth'

# config for a specific benchmark execution
class BenchmarkConfig():

    def __init__(self,
                 sw_stack: SWStackParam,
                 encryption_switch: bool,
                 integrity_switch: bool,
                 storage_level: StorageLevelParam,
                 measurement_type: MeasurementTypeParam):
        self.sw_stack = sw_stack
        self.encryption_switch = encryption_switch
        self.integrity_switch = integrity_switch
        self.storage_level = storage_level
        self.measurement_type = measurement_type
