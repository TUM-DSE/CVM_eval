# fio configuration

## Usage
```
fio --filename=/dev/vda --output-format=json ./libaio.fio
```

Note that fio supports mixing command line options and a job file. In that
case, the command line options are treated as global options of the job
file (https://git.kernel.dk/?p=fio.git;a=commit;h=bc4f5ef67d26ef98f4822d5f798cb8c4e2d2fce5)

## iouring configuration
- iou.fio: use io_uring
- iou_c.fio: use io_uring with completion polling
- iou_s.fio: use io_uring with submission polling
- iou_sc.fio: use io_uring with submission & completion polling
- libaio.fio: use libaio

