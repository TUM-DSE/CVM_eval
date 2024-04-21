# fio job files

## Usage
```
fio --filename=/dev/vda --output-format=json ./libaio.fio
```

Note that fio supports mixing command line options and a job file. In that
case, the command line options are treated as global options of the job
file (https://git.kernel.dk/?p=fio.git;a=commit;h=bc4f5ef67d26ef98f4822d5f798cb8c4e2d2fce5)

## jobfile configuration
- These job files are same except ioengine
    - [iou.fio](./iou.fio): use io_uring
    - [iou_c.fio](./iou_c.fio): use io_uring with completion polling
    - [iou_s.fio](./iou_s.fio): use io_uring with submission polling
    - [iou_sc.fio](./iou_sc.fio): use io_uring with submission & completion polling
    - [libaio.fio](./libaio.fio): use libaio
    - We refer to [Spool (ATC'20)](https://www.usenix.org/conference/atc20/presentation/xue) for the each job parameter.

