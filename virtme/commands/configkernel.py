# -*- mode: python -*-
# virtme-configkernel: Configure a kernel for virtme
# Copyright © 2014 Andy Lutomirski
# Licensed under the GPLv2, which is available in the virtme distribution
# as a file called LICENSE with SHA-256 hash:
# 8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643

import argparse
import tempfile
import os
import shutil
import subprocess
import multiprocessing
from .. import architectures

uname = os.uname()

def make_parser():
    parser = argparse.ArgumentParser(
        description='Configure a kernel for virtme',
    )

    parser.add_argument('--arch', action='store', metavar='ARCHITECTURE',
                        default=uname.machine,
                        help='Target architecture')

    g = parser.add_argument_group(title='Mode').add_mutually_exclusive_group()

    g.add_argument('--allnoconfig', action='store_true',
                        help='Overwrite configuration with a virtme-suitable allnoconfig (unlikely to work)')

    g.add_argument('--defconfig', action='store_true',
                        help='Overwrite configuration with a virtme-suitable defconfig')

    g.add_argument('--update', action='store_true',
                        help='Update existing config for virtme')

    return parser

_ARGPARSER = make_parser()

def arg_fail(message):
    print(message)
    _ARGPARSER.print_usage()
    exit(1)

_GENERIC_CONFIG = [
    '# Generic',
    'CONFIG_UEVENT_HELPER=n',	# Obsolete and slow
    'CONFIG_VIRTIO=y',
    'CONFIG_VIRTIO_PCI=y',
    'CONFIG_VIRTIO_MMIO=y',
    'CONFIG_NET=y',
    'CONFIG_NET_CORE=y',
    'CONFIG_NETDEVICES=y',
    'CONFIG_NETWORK_FILESYSTEMS=y',
    'CONFIG_INET=y',
    'CONFIG_NET_9P=y',
    'CONFIG_NET_9P_VIRTIO=y',
    'CONFIG_9P_FS=y',
    'CONFIG_VIRTIO_NET=y',
    'CONFIG_CMDLINE_OVERRIDE=n',
    'CONFIG_BINFMT_SCRIPT=y',
    'CONFIG_SHMEM=y',
    'CONFIG_TMPFS=y',
    'CONFIG_UNIX=y',
    'CONFIG_MODULE_SIG_FORCE=n',
    'CONFIG_DEVTMPFS=y',
    'CONFIG_TTY=y',
    'CONFIG_VT=y',
    'CONFIG_UNIX98_PTYS=y',
    'CONFIG_EARLY_PRINTK=y',
    '',
    '# virtio-scsi support',
    'CONFIG_BLOCK=y',
    'CONFIG_SCSI_LOWLEVEL=y',
    'CONFIG_SCSI=y',
    'CONFIG_SCSI_VIRTIO=y',
    'CONFIG_BLK_DEV_SD=y',
    '',
    '# virt-serial support',
    'CONFIG_VIRTIO_CONSOLE=y',
    '',
    '# watchdog (useful for test scripts)',
    'CONFIG_WATCHDOG=y',
    'CONFIG_WATCHDOG_CORE=y',
    'CONFIG_I6300ESB_WDT=y',
]

def main():
    args = _ARGPARSER.parse_args()
    kernel_source_prefix = "./"
    if os.path.islink('source'):
        kernel_source_prefix = 'source/'
    if not os.path.isfile(kernel_source_prefix + 'scripts/kconfig/merge_config.sh'):
        print('virtme-configkernel must be run in a kernel source or a kernel build directory')
        return 1

    arch = architectures.get(args.arch)

    conf = (_GENERIC_CONFIG +
            ['# Arch-specific options'] +
            arch.config_base())

    if shutil.which('%s-linux-gnu-gcc' % arch.gccname):
        conf.append('CONFIG_CROSS_COMPILE="%s-linux-gnu-"' % arch.gccname)

    if args.allnoconfig:
        maketarget = 'allnoconfig'
        updatetarget = 'silentoldconfig'
    elif args.defconfig:
        maketarget = arch.defconfig_target
        updatetarget = 'olddefconfig'
    elif args.update:
        maketarget = None
        updatetarget = 'olddefconfig'
    else:
        arg_fail('No mode selected')

    # TODO: Get rid of most of the noise and check the result.

    # Set up an initial config
    if maketarget:
        subprocess.check_call(['make', 'ARCH=%s' % arch.linuxname, maketarget])

    with open('.config', 'ab') as conffile:
        conffile.write('\n'.join(conf).encode('utf-8'))

    subprocess.check_call(['make', 'ARCH=%s' % arch.linuxname, updatetarget])

    print("Configured.  Build with 'make ARCH=%s -j%d'" %
          (arch.linuxname, multiprocessing.cpu_count()))

    return 0

if __name__ == '__main__':
    exit(main())
