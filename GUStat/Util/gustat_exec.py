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
            '-0', '--zero_hide', action='store_true',
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
            '-Sc', '--sys_cpu', action='store_true',
            default=False,
            help='System CPU information (/proc/cpuinfo)')

        # ... system stats: load average
        self.__oArgumentParser.add_argument(
            '-Sl', '--sys_load', action='store_true',
            default=False,
            help='System load average (/proc/loadavg)')

        # ... system stats: misc. kernel statistics
        self.__oArgumentParser.add_argument(
            '-Ss', '--sys_stat', action='store_true',
            default=False,
            help='System kernel statistics (/proc/stat)')
        self.__oArgumentParser.add_argument(
            '-Ssl', '--sys_stat_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System kernel statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Ssd', '--sys_stat_dtl', action='store_true',
            default=False,
            help='System kernel statistics: show detailed (CPU) statistics')

        # ... system stats: memory information
        self.__oArgumentParser.add_argument(
            '-Sm', '--sys_mem', action='store_true',
            default=False,
            help='System memory information (/proc/meminfo)')
        self.__oArgumentParser.add_argument(
            '-Sml', '--sys_mem_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System memory information: level (0=standard, 1=advanced, 2=expert)')

        # ... system stats: virtual memory statistics
        self.__oArgumentParser.add_argument(
            '-Sv', '--sys_vm', action='store_true',
            default=False,
            help='System virtual memory statistics (/proc/vmstat)')
        self.__oArgumentParser.add_argument(
            '-Svl', '--sys_vm_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System virtual memory statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... system stats: disks statistics
        self.__oArgumentParser.add_argument(
            '-Sd', '--sys_dsks', action='store_true',
            default=False,
            help='System disks statistics (/proc/diskstats)')
        self.__oArgumentParser.add_argument(
            '-Sdl', '--sys_dsks_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System disks statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Sdd', '--sys_dsks_dev', type=str,
            metavar='<level>',
            default=None,
            help='System disks statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Sdp', '--sys_dsks_pfx', action='store_true',
            default=False,
            help='System disks statistics: match device name prefix')

        # ... system stats: mounts statistics
        self.__oArgumentParser.add_argument(
            '-St', '--sys_mnts', action='store_true',
            default=False,
            help='System mounts statistics (/proc/self/mountstats)')
        self.__oArgumentParser.add_argument(
            '-Stl', '--sys_mnts_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System mounts statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Std', '--sys_mnts_dev', type=str,
            metavar='<device>',
            default=None,
            help='System mounts statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Stp', '--sys_mnts_pfx', action='store_true',
            default=False,
            help='System mounts statistics: match device name prefix')

        # ... system stats: network statistics
        self.__oArgumentParser.add_argument(
            '-Sn', '--sys_net', action='store_true',
            default=False,
            help='System network statistics (/proc/net/dev)')
        self.__oArgumentParser.add_argument(
            '-Snl', '--sys_net_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System network statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Snd', '--sys_net_dev', type=str,
            metavar='<device>',
            default=None,
            help='System network statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Snp', '--sys_net_pfx', action='store_true',
            default=False,
            help='System network statistics: match device name prefix')

        # ... system stats: all
        self.__oArgumentParser.add_argument(
            '-Sa', '--sys_all', action='store_true',
            default=False,
            help='System statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Sal', '--sys_all_lvl', type=int,
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
            '-Pu', '--proc_status', action='store_true',
            default=False,
            help='Process status (/proc/<pid>/status)')
        self.__oArgumentParser.add_argument(
            '-Pul', '--proc_status_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process status: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: statistics
        self.__oArgumentParser.add_argument(
            '-Ps', '--proc_stat', action='store_true',
            default=False,
            help='Process statistics (/proc/<pid>/stat)')
        self.__oArgumentParser.add_argument(
            '-Psl', '--proc_stat_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: I/Os
        self.__oArgumentParser.add_argument(
            '-Pi', '--proc_io', action='store_true',
            default=False,
            help='Process I/Os statistics (/proc/<pid>/io)')
        self.__oArgumentParser.add_argument(
            '-Pil', '--proc_io_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process I/Os statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... process stats: all
        self.__oArgumentParser.add_argument(
            '-Pa', '--proc_all', action='store_true',
            default=False,
            help='Process statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Pal', '--proc_all_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: global level (0=standard, 1=advanced, 2=expert)')

        # ... Libvirt stats: VMs
        self.__oArgumentParser.add_argument(
            '-V', '--virt', type=str,
            metavar='<vm>[,<vm> ...]',
            default=None,
            help='Libvirt statistics: comma-separated list of guests (VMs)')

        # ... Libvirt stats: Qemu block devices statistics
        self.__oArgumentParser.add_argument(
            '-Vb', '--virt_blks', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics (info blockstats)')
        self.__oArgumentParser.add_argument(
            '-Vbl', '--virt_blks_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt/Qemu block devices statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Vbd', '--virt_blks_dev', type=str,
            metavar='<device>',
            default=None,
            help='Libvirt/Qemu block devices statistics: device name')
        self.__oArgumentParser.add_argument(
            '-Vbp', '--virt_blks_pfx', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics: match device name prefix')

        # ... Libvirt stats: all
        self.__oArgumentParser.add_argument(
            '-Va', '--virt_all', action='store_true',
            default=False,
            help='Libvirt statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Val', '--virt_all_lvl', type=int,
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
        iStats_sys_all_lvl = self.__oArguments.sys_all_lvl
        bStats_sys_cpu = bStats_sys_all or self.__oArguments.sys_cpu
        iLevel_sys_cpu = iStats_sys_all_lvl
        bStats_sys_load = bStats_sys_all or self.__oArguments.sys_load
        iLevel_sys_load = iStats_sys_all_lvl
        bStats_sys_stat = bStats_sys_all or self.__oArguments.sys_stat
        iLevel_sys_stat = max(iStats_sys_all_lvl, self.__oArguments.sys_stat_lvl)
        bDetail_sys_stat = self.__oArguments.sys_stat_dtl
        bStats_sys_mem = bStats_sys_all or self.__oArguments.sys_mem
        iLevel_sys_mem = max(iStats_sys_all_lvl, self.__oArguments.sys_mem_lvl)
        bStats_sys_vm = bStats_sys_all or self.__oArguments.sys_vm
        iLevel_sys_vm = max(iStats_sys_all_lvl, self.__oArguments.sys_vm_lvl)
        bStats_sys_dsks = bStats_sys_all or self.__oArguments.sys_dsks
        iLevel_sys_dsks = max(iStats_sys_all_lvl, self.__oArguments.sys_dsks_lvl)
        sDevice_sys_dsks = self.__oArguments.sys_dsks_dev
        bPrefix_sys_dsks = self.__oArguments.sys_dsks_pfx
        bStats_sys_mnts = bStats_sys_all or self.__oArguments.sys_mnts
        iLevel_sys_mnts = max(iStats_sys_all_lvl, self.__oArguments.sys_mnts_lvl)
        sDevice_sys_mnts = self.__oArguments.sys_mnts_dev
        bPrefix_sys_mnts = self.__oArguments.sys_mnts_pfx
        bStats_sys_net = bStats_sys_all or self.__oArguments.sys_net
        iLevel_sys_net = max(iStats_sys_all_lvl, self.__oArguments.sys_net_lvl)
        sDevice_sys_net = self.__oArguments.sys_net_dev
        bPrefix_sys_net = self.__oArguments.sys_net_pfx

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
        iStats_proc_all_lvl = self.__oArguments.proc_all_lvl
        bStats_proc_status = bStats_proc_all or self.__oArguments.proc_status
        iLevel_proc_status = max(iStats_proc_all_lvl, self.__oArguments.proc_status_lvl)
        bStats_proc_stat = bStats_proc_all or self.__oArguments.proc_stat
        iLevel_proc_stat = max(iStats_proc_all_lvl, self.__oArguments.proc_stat_lvl)
        bStats_proc_io = bStats_proc_all or self.__oArguments.proc_io
        iLevel_proc_io = max(iStats_proc_all_lvl, self.__oArguments.proc_io_lvl)

        # ... libvirt statistics
        lGuests = list()
        if self.__oArguments.virt is not None:
            lGuests = self.__oArguments.virt.strip(',').split(',')
        bStats_virt_all = self.__oArguments.virt_all
        iStats_virt_all_lvl = self.__oArguments.virt_all_lvl
        bStats_virt_blks = bStats_virt_all or self.__oArguments.virt_blks
        iLevel_virt_blks = max(iStats_virt_all_lvl, self.__oArguments.virt_blks_lvl)
        sDevice_virt_blks = self.__oArguments.virt_blks_dev
        bPrefix_virt_blks = self.__oArguments.virt_blks_pfx


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
        if bStats_sys_dsks:
            oGUStatData_1.parseStat_sys_dsks(iLevel_sys_dsks, sDevice_sys_dsks, bPrefix_sys_dsks)
        if bStats_sys_mnts:
            oGUStatData_1.parseStat_sys_mnts(iLevel_sys_mnts, sDevice_sys_mnts, bPrefix_sys_mnts)
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
            if bStats_sys_dsks:
                oGUStatData_2.parseStat_sys_dsks(iLevel_sys_dsks, sDevice_sys_dsks, bPrefix_sys_dsks)
            if bStats_sys_mnts:
                oGUStatData_2.parseStat_sys_mnts(iLevel_sys_mnts, sDevice_sys_mnts, bPrefix_sys_mnts)
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

