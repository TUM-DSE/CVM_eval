from bm import params

import subprocess as sp

def cleanup():
    # unmap encryption from disk, if applicable (hence do not check return code)
    for disk_map in params.MAP_NAMES:
        sp.run(['sudo', 'cryptsetup', 'remove', disk_map])
