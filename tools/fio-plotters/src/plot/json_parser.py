from dataclasses import dataclass
import json

import pandas as pd

ENV_BM  = 'bare-metal'
ENV_VM  = 'native-vm'
ENV_SEV = 'sev'
ENVS    = [ENV_BM, ENV_VM, ENV_SEV]

DEV_KERNEL      = 'kernel'
DEV_VIRTIO_BLK  = 'virtio-blk'
DEV_VIRTIO_SCSI = 'virtio-scsi'
DEVS            = [DEV_KERNEL, DEV_VIRTIO_BLK, DEV_VIRTIO_SCSI]

MT_BW   = 'bw'
MT_ALAT = 'avg-lat'
MT_IOPS = 'iops'
MTS     = [MT_BW, MT_ALAT, MT_IOPS]

FS_SEP        = '/'
MT_REV_INDEX  = -2
DEV_REV_INDEX = -3
ENV_REV_INDEX = -4

JOB_KEY                            = 'jobs'
JOB_JOBOPTS_KEY                    = 'job options'
JOB_JOBOPTS_RW_KEY                 = 'rw'
JOB_WRITE_KEY                      = 'write'
JOB_READ_KEY                       = 'read'

JOB_R_W_BW_KEY   = 'bw'
JOB_R_W_IOPS_KEY = 'iops'
JOB_R_W_ALAT_KEY = 'lat_ns'
JOB_R_W_ALAT_MEAN_KEY = 'mean'


@dataclass
class JobContext:
    job:     dict
    device:  str
    env:     str


# row format:
# mt : iot (grouped), (unique triplet) env, device, mt_res
# e.g. bw, bare-metal, kernel, 123
def parse_ctxs(mt_job_ctxs):
    res_d = {}
    for mt, job_ctxs in mt_job_ctxs.items():
        if mt not in res_d.keys():
            res_d[mt] = {}

        for job_ctx in job_ctxs:

            job = job_ctx.job
            io_type = job[JOB_JOBOPTS_KEY][JOB_JOBOPTS_RW_KEY]

            if mt == MT_BW:
                mt_res_key = JOB_R_W_BW_KEY
            elif mt == MT_IOPS:
                mt_res_key = JOB_R_W_IOPS_KEY
            elif mt == MT_ALAT:
                mt_res_key = JOB_R_W_ALAT_KEY
            else:
                assert False, f"invalid mt: {mt}"
            # r/w my be e.g. randread; need to check if r or w
            if JOB_WRITE_KEY in io_type:
                iot_key = JOB_WRITE_KEY
            elif JOB_READ_KEY in io_type:
                iot_key = JOB_READ_KEY
            else:
                assert False, f"could not identify if iotype is r/w: {io_type}"

            # requires extra key
            if mt == MT_ALAT:
                mt_res = job[iot_key][mt_res_key][JOB_R_W_ALAT_MEAN_KEY]
            else:
                mt_res = job[iot_key][mt_res_key]

            # round
            mt_res = round(mt_res)

            if io_type not in res_d[mt]:
                res_d[mt][io_type] = []

            res_d[mt][io_type].append([job_ctx.env, job_ctx.device, mt_res])

    return pd.DataFrame.from_dict(res_d)


# parses job context from file path
# NOTE: file paths MUST fit following format:
# .../env/device/io_type/job.json
# group by measurement type
def extract_jobctxs(input_files):
    mt_job_ctxs = {}
    for f_p in input_files:
        f_a = f_p.split('/')
        mt = f_a[MT_REV_INDEX]
        if mt not in MTS:
            assert False, f"invalid mt {mt}"
        dev = f_a[DEV_REV_INDEX]
        if dev not in DEVS:
            assert False, f"invalid dev {dev}"
        env = f_a[ENV_REV_INDEX]
        if env not in ENVS:
            assert False, f"invalid env {env}"
        with open(f_p, 'r') as f:
            fio_json = json.load(f)
            for job in fio_json[JOB_KEY]:
                job_ctx = JobContext(job, dev, env)
                if mt in mt_job_ctxs.keys():
                    mt_job_ctxs[mt].append(job_ctx)
                else:
                    mt_job_ctxs[mt] = [job_ctx]

    return mt_job_ctxs

def parse(input_files):
    mt_job_ctxs = extract_jobctxs(input_files)
    return parse_ctxs(mt_job_ctxs)


