import enum
import os

RAMDISK_PATH = '/dev/ram0'
ENCRYPTED_RAM_MAP_NAME = 'encrypted-ram'
ENCRYPTED_RAM_MAP_PATH = os.path.join('/dev', 'mapper', ENCRYPTED_RAM_MAP_NAME)
INTEGRITY_RAM_MAP_NAME = 'integrity-ram'
INTEGRITY_RAM_MAP_PATH = os.path.join('/dev', 'mapper', INTEGRITY_RAM_MAP_NAME)
ENCRYPTED_INTEGRITY_RAM_MAP_NAME = 'encrypted-integrity-ram'
ENCRYPTED_INTEGRITY_RAM_MAP_PATH = os.path.join('/dev', 'mapper', ENCRYPTED_INTEGRITY_RAM_MAP_NAME)

MAP_NAMES = [ENCRYPTED_RAM_MAP_NAME, INTEGRITY_RAM_MAP_NAME, ENCRYPTED_INTEGRITY_RAM_MAP_NAME]

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
                 measurement_type: MeasurementTypeParam,
                 target_disk=RAMDISK_PATH,
                 encrypted_target_disk=ENCRYPTED_RAM_MAP_PATH,
                 integrity_target_disk=INTEGRITY_RAM_MAP_PATH,
                 encrypted_integrity_target_disk=ENCRYPTED_INTEGRITY_RAM_MAP_PATH):
        self.sw_stack = sw_stack
        self.encryption_switch = encryption_switch
        self.integrity_switch = integrity_switch
        self.storage_level = storage_level
        self.measurement_type = measurement_type
        self.target_disk = target_disk
        self.encrypted_target_disk = ENCRYPTED_RAM_MAP_PATH
        self.integrity_target_disk = integrity_target_disk
        self.encrypted_integrity_target_disk = encrypted_integrity_target_disk
