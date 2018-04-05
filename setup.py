#!/usr/bin/env python3
# -*- mode:python; tab-width:4; c-basic-offset:4; intent-tabs-mode:nil; -*-
# ex: filetype=python tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent smartindent

# Modules
from distutils.core import setup
import os

# Helpers
def filesInDir(sDirectory):
    lsfilesInDir = list()
    for sFile in os.listdir(sDirectory):
        sFile = sDirectory.rstrip(os.sep)+os.sep+sFile
        if os.path.isfile(sFile):
            lsfilesInDir.append(sFile)
    return lsfilesInDir

# Setup
setup(
    name = 'gustat',
    description = 'Global Unified Statistics (GUStat)',
    long_description = \
        """
        The Global Unified Statistics (GUStat) library/utility is an attempt to
        gather and output Linux most-commonly-used system statistics in a unified
        and pipe-friendly way.

        The currently supported statistics sources are:
        (system-level)
         - /proc/cpuinfo
         - /proc/loadavg
         - /proc/stat
         - /proc/meminfo
         - /proc/vmstat
         - /proc/diskstats
         - /proc/self/mountstats
         - /proc/net/dev
        (process-level)
         - /proc/[pid]/status
         - /proc/[pid]/stat
         - /proc/[pid]/io
        (libvirt-level)
         - virsh qemu-monitor-command info blockstats
       """,
    version = os.environ.get('VERSION'),
    platforms = ['Linux'],
    author = 'Cedric Dufour',
    author_email = 'http://cedric.dufour.name',
    license = 'GPL-3',
    download_url = 'https://github.com/cedric-dufour/gustat',
    packages = ['GUStat', 'GUStat.Util'],
    package_dir = {'': '.'},
    requires = ['argparse'],
    scripts = ['gustat', 'guinflux'],
    )

