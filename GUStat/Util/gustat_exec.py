# -*- mode:python; tab-width:4; c-basic-offset:4; intent-tabs-mode:nil; -*-
# ex: filetype=python tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent smartindent

#
# Global Unified Statistics (GUStat)
# Copyright (C) 2014 Cedric Dufour <http://cedric.dufour.name>
# Author: Cedric Dufour <http://cedric.dufour.name>
#
# The Global Unified Statistics (GUStat) is free software:
# you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, Version 3.
#
# The Global Unified Statistics (GUStat) is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details.
#

# Modules
# ... deb: python-argparse
from GUStat import \
    GUSTAT_VERSION, \
    GUStatData
import argparse as AP
import copy
import os
import signal
import sys
import textwrap
import time


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class GUStatMain:
    """
    Global Statistics Parser
    """

    #------------------------------------------------------------------------------
    # CONSTRUCTORS / DESTRUCTOR
    #------------------------------------------------------------------------------

    def __init__(self):
        # Fields
        self.__bInterrupted = False
        self.__oArgumentParser = None
        self.__oArguments = None

        # Initialization
        self.__initArgumentParser()


    def __initArgumentParser(self):
        """
        Creates the arguments parser (and help generator)
        """

        # Create argument parser
        self.__oArgumentParser = AP.ArgumentParser(
            prog = sys.argv[0].split('/')[-1],
            formatter_class = AP.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent('''\
                Refer to the Linux kernel /proc documention for details on gathered statistics:
                  man 5 proc
                 or
                  https://www.kernel.org/doc/Documentation/filesystems/proc.txt
                '''))

        # ... global: output preferences
        self.__oArgumentParser.add_argument(
            '-t', '--timestamp', action='store_true',
            default=False,
            help='Output: prefix output with timestamp')
        self.__oArgumentParser.add_argument(
            '-p', '--precision', type=int,
            metavar='<decimals>',
            default=-1,
            help='Output: decimal precision for float values')
        self.__oArgumentParser.add_argument(
            '-0', '--zero-hide', action='store_true',
            default=False,
            help='Output: do not show zero values')
        self.__oArgumentParser.add_argument(
            '-j', '--justify', type=int,
            metavar='<width>',
            default=-1,
            help='Output: justify output width, in characters (0=autodetect)')
        self.__oArgumentParser.add_argument(
            '-s', '--thousands', action='store_true',
            default=False,
            help='Output: display thousands separator (justify mode only)')
        self.__oArgumentParser.add_argument(
            '-o', '--top', action='store_true',
            default=False,
            help='Output: always start output at top of screen')

        # ... global: interval mode
        self.__oArgumentParser.add_argument(
            '-i', '--interval', type=int,
            metavar='<seconds>',
            default=0,
            help='Interval: statistics gathering interval, in seconds [s]')
        self.__oArgumentParser.add_argument(
            '-c', '--continuous', action='store_true',
            default=False,
            help='Interval: continuous statistics gathering')
        self.__oArgumentParser.add_argument(
            '-d', '--differential', action='store_true',
            default=False,
            help='Interval: display differences relative to start of sampling rather than last interval')
        self.__oArgumentParser.add_argument(
            '-r', '--raw', action='store_true',
            default=False,
            help='Interval: display raw differences rather than rates')

        # ... system stats: CPU information
        self.__oArgumentParser.add_argument(
            '-Sc', '--sys-cpu', action='store_true',
            default=False,
            help='System CPU information (/proc/cpuinfo)')
        self.__oArgumentParser.add_argument(
            '-Scl', '--sys-cpu-level', type=int,
            metavar='<level>',
            default=0,
            help='System CPU information: level (0=standard, 1=advanced, 2=expert)')

        # ... system stats: load average
        self.__oArgumentParser.add_argument(
            '-Sl', '--sys-load', action='store_true',
            default=False,
            help='System load average (/proc/loadavg)')

        # ... system stats: misc. kernel statistics
        self.__oArgumentParser.add_argument(
            '-Ss', '--sys-stat', action='store_true',
            default=False,
            help='System kernel statistics (/proc/stat)')
        self.__oArgumentParser.add_argument(
            '-Ssl', '--sys-stat-level', type=int,
            metavar='<level>',
            default=0,
            help='System kernel statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Ssd', '--sys-stat-detail', action='store_true',
            default=False,
            help='System kernel statistics: show detailed (CPU) statistics')

        # ... system stats: memory information
        self.__oArgumentParser.add_argument(
            '-Sm', '--sys-mem', action='store_true',
            default=False,
            help='System memory information (/proc/meminfo)')
        self.__oArgumentParser.add_argument(
            '-Sml', '--sys-mem-level', type=int,
            metavar='<level>',
            default=0,
            help='System memory information: level (0=standard, 1=advanced, 2=expert)')

        # ... system stats: virtual memory statistics
        self.__oArgumentParser.add_argument(
            '-Sv', '--sys-vm', action='store_true',
            default=False,
            help='System virtual memory statistics (/proc/vmstat)')
        self.__oArgumentParser.add_argument(
            '-Svl', '--sys-vm-level', type=int,
            metavar='<level>',
            default=0,
            help='System virtual memory statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... system stats: disks statistics
        self.__oArgumentParser.add_argument(
            '-Sd', '--sys-disk', action='store_true',
            default=False,
            help='System disks statistics (/proc/diskstats)')
        self.__oArgumentParser.add_argument(
            '-Sdl', '--sys-disk-level', type=int,
            metavar='<level>',
            default=0,
            help='System disks statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Sdd', '--sys-disk-device', type=str,
            metavar='<level>',
            default=None,
            help='System disks statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Sdp', '--sys-disk-prefix', action='store_true',
            default=False,
            help='System disks statistics: match device name prefix')

        # ... system stats: mounts statistics
        self.__oArgumentParser.add_argument(
            '-St', '--sys-mount', action='store_true',
            default=False,
            help='System mounts statistics (/proc/self/mountstats)')
        self.__oArgumentParser.add_argument(
            '-Stl', '--sys-mount-level', type=int,
            metavar='<level>',
            default=0,
            help='System mounts statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Std', '--sys-mount-device', type=str,
            metavar='<device>',
            default=None,
            help='System mounts statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Stp', '--sys-mount-prefix', action='store_true',
            default=False,
            help='System mounts statistics: match device name prefix')

        # ... system stats: network statistics
        self.__oArgumentParser.add_argument(
            '-Sn', '--sys-net', action='store_true',
            default=False,
            help='System network statistics (/proc/net/dev)')
        self.__oArgumentParser.add_argument(
            '-Snl', '--sys-net-level', type=int,
            metavar='<level>',
            default=0,
            help='System network statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Snd', '--sys-net-device', type=str,
            metavar='<device>',
            default=None,
            help='System network statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Snp', '--sys-net-prefix', action='store_true',
            default=False,
            help='System network statistics: match device name prefix')

        # ... system stats: all
        self.__oArgumentParser.add_argument(
            '-Sa', '--sys-all', action='store_true',
            default=False,
            help='System statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Sal', '--sys-all-level', type=int,
            metavar='<level>',
            default=0,
            help='System statistics: global level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: PIDs
        self.__oArgumentParser.add_argument(
            '-P', '--process', type=str,
            metavar='<pid>[,<pid> ...]',
            default=None,
            help='Process statistics: comma-separated list of process PIDs; \'*\' for all')

        # ... process stats: status
        self.__oArgumentParser.add_argument(
            '-Pu', '--proc-status', action='store_true',
            default=False,
            help='Process status (/proc/<pid>/status)')
        self.__oArgumentParser.add_argument(
            '-Pul', '--proc-status-level', type=int,
            metavar='<level>',
            default=0,
            help='Process status: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: statistics
        self.__oArgumentParser.add_argument(
            '-Ps', '--proc-stat', action='store_true',
            default=False,
            help='Process statistics (/proc/<pid>/stat)')
        self.__oArgumentParser.add_argument(
            '-Psl', '--proc-stat-level', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: I/Os
        self.__oArgumentParser.add_argument(
            '-Pi', '--proc-io', action='store_true',
            default=False,
            help='Process I/Os statistics (/proc/<pid>/io)')
        self.__oArgumentParser.add_argument(
            '-Pil', '--proc-io-level', type=int,
            metavar='<level>',
            default=0,
            help='Process I/Os statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: all
        self.__oArgumentParser.add_argument(
            '-Pa', '--proc-all', action='store_true',
            default=False,
            help='Process statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Pal', '--proc-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: global level (0=standard, 1=advanced, 2=expert)')

        # ... Libvirt stats: VMs
        self.__oArgumentParser.add_argument(
            '-V', '--virt', type=str,
            metavar='<vm>[,<vm> ...]',
            default=None,
            help='Libvirt statistics: comma-separated list of guests (VMs); \'*\' for all')

        # ... Libvirt stats: Qemu block devices statistics
        self.__oArgumentParser.add_argument(
            '-Vb', '--virt-blks', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics (info blockstats)')
        self.__oArgumentParser.add_argument(
            '-Vbl', '--virt-blks-level', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt/Qemu block devices statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Vbd', '--virt-blks-device', type=str,
            metavar='<device>',
            default=None,
            help='Libvirt/Qemu block devices statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Vbp', '--virt-blks-prefix', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics: match device name prefix')

        # ... Libvirt stats: all
        self.__oArgumentParser.add_argument(
            '-Va', '--virt-all', action='store_true',
            default=False,
            help='Libvirt statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Val', '--virt-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt statistics: global level (0=standard, 1=advanced, 2=expert)')

        # ... other
        self.__oArgumentParser.add_argument(
            '-v', '--version', action='version',
            version=('GUStat - %s - Cedric Dufour <http://cedric.dufour.name>\n' % GUSTAT_VERSION))


    def __initArguments(self, _aArguments = None):
        """
        Parses the command-line arguments; returns a non-zero exit code in case of failure.
        """

        # Parse arguments
        if _aArguments is None:
            _aArguments = sys.argv
        try:
            self.__oArguments = self.__oArgumentParser.parse_args()
        except Exception as e:
            self.__oArguments = None
            sys.stderr.write('ERROR: Failed to parse arguments; %s\n' % str(e))
            return 1

        return 0


    #------------------------------------------------------------------------------
    # METHODS
    #------------------------------------------------------------------------------

    #
    # Helpers
    #

    # Shamelessly copied from http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    def __getTerminalSize(self):
        """
        Retrieve the console terminal window size
        """

        env = os.environ
        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct, os
                cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            except:
                return
            return cr
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
        return int(cr[1]), int(cr[0])


    #
    # Main
    #

    def __signal(self, signal, frame):
        self.__bInterrupted = True


    def execute(self):
        """
        Executes the Global Statistics parser; returns a non-zero exit code in case of failure.
        """

        # Parse arguments
        iReturn = self.__initArguments()
        if iReturn:
            return iReturn

        # ... output formatting
        bTimestamp = self.__oArguments.timestamp
        sTimestamp = None
        sIntFormat = '{:}'
        sFloatFormat = '{:}'
        if self.__oArguments.precision >= 0:
            sFloatFormat = sFloatFormat.replace(':', ':.'+str(self.__oArguments.precision)+'f')
        bZeroHide = self.__oArguments.zero_hide
        iJustify = self.__oArguments.justify
        bTop = self.__oArguments.top
        if bTop and iJustify < 0:
            iJustify = 0
        if iJustify == 0:
            (iWidth, iHeight) = self.__getTerminalSize()
            iJustify = iWidth
        if iJustify < 40:
            bTop = False
            iJustify = -1
        if iJustify > 0 and self.__oArguments.thousands:
            sIntFormat = sIntFormat.replace(':', ':,')
            sFloatFormat = sFloatFormat.replace(':', ':,')
        if sIntFormat == '{:}':
            sIntFormat = None
        if sFloatFormat == '{:}':
            sFloatFormat = None

        # ... interval mode
        bInterval = False
        bContinuous = False
        bDifferential = False
        bRaw = False
        if self.__oArguments.interval > 0:
            bInterval = True
            bContinuous = self.__oArguments.continuous
            bDifferential = self.__oArguments.differential
            bRaw = self.__oArguments.raw

        # ... system statistics
        bStats_sys_all = self.__oArguments.sys_all
        iStats_sys_all_level = self.__oArguments.sys_all_level
        bStats_sys_cpu = bStats_sys_all or self.__oArguments.sys_cpu
        iLevel_sys_cpu = max(iStats_sys_all_level, self.__oArguments.sys_cpu_level)
        bStats_sys_load = bStats_sys_all or self.__oArguments.sys_load
        iLevel_sys_load = iStats_sys_all_level
        bStats_sys_stat = bStats_sys_all or self.__oArguments.sys_stat
        iLevel_sys_stat = max(iStats_sys_all_level, self.__oArguments.sys_stat_level)
        bDetail_sys_stat = self.__oArguments.sys_stat_detail
        bStats_sys_mem = bStats_sys_all or self.__oArguments.sys_mem
        iLevel_sys_mem = max(iStats_sys_all_level, self.__oArguments.sys_mem_level)
        bStats_sys_vm = bStats_sys_all or self.__oArguments.sys_vm
        iLevel_sys_vm = max(iStats_sys_all_level, self.__oArguments.sys_vm_level)
        bStats_sys_disk = bStats_sys_all or self.__oArguments.sys_disk
        iLevel_sys_disk = max(iStats_sys_all_level, self.__oArguments.sys_disk_level)
        sDevice_sys_disk = self.__oArguments.sys_disk_device
        bPrefix_sys_disk = self.__oArguments.sys_disk_prefix
        bStats_sys_mount = bStats_sys_all or self.__oArguments.sys_mount
        iLevel_sys_mount = max(iStats_sys_all_level, self.__oArguments.sys_mount_level)
        sDevice_sys_mount = self.__oArguments.sys_mount_device
        bPrefix_sys_mount = self.__oArguments.sys_mount_prefix
        bStats_sys_net = bStats_sys_all or self.__oArguments.sys_net
        iLevel_sys_net = max(iStats_sys_all_level, self.__oArguments.sys_net_level)
        sDevice_sys_net = self.__oArguments.sys_net_device
        bPrefix_sys_net = self.__oArguments.sys_net_prefix

        # ... processes statistics
        lPids = list()
        if self.__oArguments.process is not None:
            if self.__oArguments.process == '*':
                from glob import glob
                lPids = sorted(list(map(lambda s: int(s.rsplit('/', 1)[1]), glob('/proc/[0-9]*'))))
            else:
                lPids = self.__oArguments.process.strip(',').split(',')
            try:
                list(map(int, lPids))
            except:
                sys.stderr.write('ERROR: Invalid process PIDs; %s\n' % self.__oArguments.process)
                return 1
        bStats_proc_all = self.__oArguments.proc_all
        iStats_proc_all_level = self.__oArguments.proc_all_level
        bStats_proc_status = bStats_proc_all or self.__oArguments.proc_status
        iLevel_proc_status = max(iStats_proc_all_level, self.__oArguments.proc_status_level)
        bStats_proc_stat = bStats_proc_all or self.__oArguments.proc_stat
        iLevel_proc_stat = max(iStats_proc_all_level, self.__oArguments.proc_stat_level)
        bStats_proc_io = bStats_proc_all or self.__oArguments.proc_io
        iLevel_proc_io = max(iStats_proc_all_level, self.__oArguments.proc_io_level)

        # ... libvirt statistics
        lGuests = list()
        if self.__oArguments.virt is not None:
            if self.__oArguments.virt == '*':
                from subprocess import check_output
                lCommandArgs = ['virsh', '--quiet', 'list', '--name']
                try:
                    lGuests = sorted(check_output(lCommandArgs).decode(sys.stdout.encoding).splitlines())
                except:
                    sys.stderr.write('ERROR: Command failed; %s\n' % ' '.join(lCommandArgs))
            else:
                lGuests = self.__oArguments.virt.strip(',').split(',')
        bStats_virt_all = self.__oArguments.virt_all
        iStats_virt_all_level = self.__oArguments.virt_all_level
        bStats_virt_blks = bStats_virt_all or self.__oArguments.virt_blks
        iLevel_virt_blks = max(iStats_virt_all_level, self.__oArguments.virt_blks_level)
        sDevice_virt_blks = self.__oArguments.virt_blks_device
        bPrefix_virt_blks = self.__oArguments.virt_blks_prefix


        # Signal handling
        signal.signal(signal.SIGINT, self.__signal)
        signal.signal(signal.SIGTERM, self.__signal)

        # Parse statistics

        # ... timestamp
        if bTimestamp:
            sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        # ... gather statistics
        oGUStatData_1 = GUStatData(bInterval, not bRaw)
        if bStats_sys_cpu:
            oGUStatData_1.parseStat_sys_cpu(iLevel_sys_cpu)
        if bStats_sys_load:
            oGUStatData_1.parseStat_sys_load(iLevel_sys_load)
        if bStats_sys_stat:
            oGUStatData_1.parseStat_sys_stat(iLevel_sys_stat, bDetail_sys_stat)
        if bStats_sys_mem:
            oGUStatData_1.parseStat_sys_mem(iLevel_sys_mem)
        if bStats_sys_vm:
            oGUStatData_1.parseStat_sys_vm(iLevel_sys_vm)
        if bStats_sys_disk:
            oGUStatData_1.parseStat_sys_disk(iLevel_sys_disk, sDevice_sys_disk, bPrefix_sys_disk)
        if bStats_sys_mount:
            oGUStatData_1.parseStat_sys_mount(iLevel_sys_mount, sDevice_sys_mount, bPrefix_sys_mount)
        if bStats_sys_net:
            oGUStatData_1.parseStat_sys_net(iLevel_sys_net, sDevice_sys_net, bPrefix_sys_net)
        for iPid in lPids:
            if bStats_proc_status:
                oGUStatData_1.parseStat_proc_status(iLevel_proc_status, iPid)
            if bStats_proc_stat:
                oGUStatData_1.parseStat_proc_stat(iLevel_proc_stat, iPid)
            if bStats_proc_io:
                oGUStatData_1.parseStat_proc_io(iLevel_proc_io, iPid)
        for sGuest in lGuests:
            if bStats_virt_blks:
                oGUStatData_1.parseStat_virt_blks(iLevel_virt_blks, sGuest, sDevice_virt_blks, bPrefix_virt_blks)

        # ... display statistics
        if not bInterval:
            try:
                oGUStatData_1.display(sTimestamp, sIntFormat, sFloatFormat, bZeroHide, iJustify)
            except:
                return 0
            return 0


        # Interval mode
        oGUStatData_2 = GUStatData(bInterval, not bRaw)
        oGUStatData_D = GUStatData(bInterval, not bRaw)
        iIntervalCount = 0
        while True:
            time.sleep(self.__oArguments.interval)
            iIntervalCount += 1

            # ... timestamp
            if bTimestamp:
                sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            # ... gather statistics
            if bStats_sys_cpu:
                oGUStatData_2.parseStat_sys_cpu(iLevel_sys_cpu)
            if bStats_sys_load:
                oGUStatData_2.parseStat_sys_load(iLevel_sys_load)
            if bStats_sys_stat:
                oGUStatData_2.parseStat_sys_stat(iLevel_sys_stat, bDetail_sys_stat)
            if bStats_sys_mem:
                oGUStatData_2.parseStat_sys_mem(iLevel_sys_mem)
            if bStats_sys_vm:
                oGUStatData_2.parseStat_sys_vm(iLevel_sys_vm)
            if bStats_sys_disk:
                oGUStatData_2.parseStat_sys_disk(iLevel_sys_disk, sDevice_sys_disk, bPrefix_sys_disk)
            if bStats_sys_mount:
                oGUStatData_2.parseStat_sys_mount(iLevel_sys_mount, sDevice_sys_mount, bPrefix_sys_mount)
            if bStats_sys_net:
                oGUStatData_2.parseStat_sys_net(iLevel_sys_net, sDevice_sys_net, bPrefix_sys_net)
            for iPid in lPids:
                if bStats_proc_status:
                    oGUStatData_2.parseStat_proc_status(iLevel_proc_status, iPid)
                if bStats_proc_stat:
                    oGUStatData_2.parseStat_proc_stat(iLevel_proc_stat, iPid)
                if bStats_proc_io:
                    oGUStatData_2.parseStat_proc_io(iLevel_proc_io, iPid)
            for sGuest in lGuests:
                if bStats_virt_blks:
                    oGUStatData_2.parseStat_virt_blks(iLevel_virt_blks, sGuest, sDevice_virt_blks, bPrefix_virt_blks)

            # ... compute differences
            for sKey in oGUStatData_1.dStats.keys():
                if sKey not in iter(oGUStatData_2.dStats.keys()):
                    continue
                oGUStatData_D.dStats[sKey] = \
                    copy.deepcopy(oGUStatData_2.dStats[sKey])
                oGUStatData_D.dStats[sKey]['value'] = float(
                    oGUStatData_2.dStats[sKey]['value'] -
                    oGUStatData_1.dStats[sKey]['value'])
                if not bRaw:
                    oGUStatData_D.dStats[sKey]['unit'] += '/s'
                    oGUStatData_D.dStats[sKey]['value'] /= self.__oArguments.interval
                    if bDifferential:
                        oGUStatData_D.dStats[sKey]['value'] /= iIntervalCount
                if not bDifferential:
                    oGUStatData_1.dStats[sKey]['value'] = \
                        oGUStatData_2.dStats[sKey]['value']

            # ... display differences
            try:
                if bTop:
                    #sys.stdout.write(chr(27)+'[2J')
                    sys.stdout.write('\x1b[2J\x1b[H')
                    if sTimestamp is not None:
                        sys.stdout.write('# GUStat - %s\n' % sTimestamp)
                    else:
                        sys.stdout.write('# GUStat\n')
                    oGUStatData_D.display(None, sIntFormat, sFloatFormat, bZeroHide, iJustify)
                else:
                    oGUStatData_D.display(sTimestamp, sIntFormat, sFloatFormat, bZeroHide, iJustify)
            except:
                break

            # ... continue
            if not bContinuous or self.__bInterrupted:
                break

        return 0

