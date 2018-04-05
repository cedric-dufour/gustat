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
        self.__oArgumentParser.add_argument(
            '--exit-on-error', action='store_true',
            default=False,
            help='Output: immediately exit on error')

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

        # ... CPU statistics: general information
        self.__oArgumentParser.add_argument(
            '-Ci', '--cpu-info', action='store_true',
            default=False,
            help='CPU information (/proc/cpuinfo)')
        self.__oArgumentParser.add_argument(
            '-Cil', '--cpu-info-level', type=int,
            metavar='<level>',
            default=0,
            help='CPU information: level (0=standard, 1=advanced, 2=expert)')

        # ... CPU statistics: system load
        self.__oArgumentParser.add_argument(
            '-Cl', '--cpu-load', action='store_true',
            default=False,
            help='System load (/proc/loadavg)')

        # ... CPU statistics: detailed statistics
        self.__oArgumentParser.add_argument(
            '-Cs', '--cpu-stat', action='store_true',
            default=False,
            help='CPU statistics (/proc/stat)')
        self.__oArgumentParser.add_argument(
            '-Csl', '--cpu-stat-level', type=int,
            metavar='<level>',
            default=0,
            help='CPU statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Csd', '--cpu-stat-detail', action='store_true',
            default=False,
            help='CPU statistics: show detailed (per-CPU) statistics')

        # ... CPU statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Ca', '--cpu-all', action='store_true',
            default=False,
            help='CPU: all statistics')
        self.__oArgumentParser.add_argument(
            '-Cal', '--cpu-all-level', type=int,
            metavar='<level>',
            default=0,
            help='CPU: global level (0=standard, 1=advanced, 2=expert)')

        # ... memory statistics: general information
        self.__oArgumentParser.add_argument(
            '-Mi', '--mem-info', action='store_true',
            default=False,
            help='Memory information (/proc/meminfo)')
        self.__oArgumentParser.add_argument(
            '-Mil', '--mem-info-level', type=int,
            metavar='<level>',
            default=0,
            help='Memory information: level (0=standard, 1=advanced, 2=expert)')

        # ... memory statistics: virtual memory statistics
        self.__oArgumentParser.add_argument(
            '-Mv', '--mem-vm', action='store_true',
            default=False,
            help='Virtual memory statistics (/proc/vmstat)')
        self.__oArgumentParser.add_argument(
            '-Mvl', '--mem-vm-level', type=int,
            metavar='<level>',
            default=0,
            help='Virtual memory statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... memory statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Ma', '--mem-all', action='store_true',
            default=False,
            help='Memory: all statistics')
        self.__oArgumentParser.add_argument(
            '-Mal', '--mem-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Memory: global level (0=standard, 1=advanced, 2=expert)')

        # ... I/O statistics: disks
        self.__oArgumentParser.add_argument(
            '-Id', '--io-disk', action='store_true',
            default=False,
            help='Disks statistics (/proc/diskstats)')
        self.__oArgumentParser.add_argument(
            '-Idl', '--io-disk-level', type=int,
            metavar='<level>',
            default=0,
            help='Disks statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Idd', '--io-disk-device', type=str,
            metavar='<device>|re/<device>/',
            default=None,
            help='Disks statistics: filter by device')

        # ... I/O statistics: mounts
        self.__oArgumentParser.add_argument(
            '-Im', '--io-mount', action='store_true',
            default=False,
            help='Mounts statistics (/proc/self/mountstats)')
        self.__oArgumentParser.add_argument(
            '-Iml', '--io-mount-level', type=int,
            metavar='<level>',
            default=0,
            help='Mounts statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Imd', '--io-mount-device', type=str,
            metavar='<device>|re/<device>/',
            default=None,
            help='Mounts statistics: filter by device')
        self.__oArgumentParser.add_argument(
            '-Imt', '--io-mount-mountpoint', type=str,
            metavar='<mountpoint>|re/<mountpoint>/',
            default=None,
            help='Mounts statistics: filter by mountpoint')

        # ... I/O statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Ia', '--io-all', action='store_true',
            default=False,
            help='I/O: all statistics')
        self.__oArgumentParser.add_argument(
            '-Ial', '--io-all-level', type=int,
            metavar='<level>',
            default=0,
            help='I/O: global level (0=standard, 1=advanced, 2=expert)')

        # ... network statistics: device
        self.__oArgumentParser.add_argument(
            '-Nd', '--net-dev', action='store_true',
            default=False,
            help='Network devices statistics (/proc/net/dev)')
        self.__oArgumentParser.add_argument(
            '-Ndl', '--net-dev-level', type=int,
            metavar='<level>',
            default=0,
            help='Network devices statistics: level (0=standard, 1=advanced, 2=expert)')
        self.__oArgumentParser.add_argument(
            '-Ndd', '--net-dev-device', type=str,
            metavar='<device>|re/<device>/',
            default=None,
            help='Network devices statistics: filter by device')

        # ... network statistics: TCP
        self.__oArgumentParser.add_argument(
            '-Nt', '--net-tcp', action='store_true',
            default=False,
            help='TCP connections statistics (/proc/net/tcp)')
        self.__oArgumentParser.add_argument(
            '-Ntl', '--net-tcp-level', type=int,
            metavar='<level>',
            default=0,
            help='TCP connections statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... network statistics: UDP
        self.__oArgumentParser.add_argument(
            '-Nu', '--net-udp', action='store_true',
            default=False,
            help='UDP connections statistics (/proc/net/udp)')
        self.__oArgumentParser.add_argument(
            '-Nul', '--net-udp-level', type=int,
            metavar='<level>',
            default=0,
            help='UDP connections statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... network statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Na', '--net-all', action='store_true',
            default=False,
            help='Network: all statistics')
        self.__oArgumentParser.add_argument(
            '-Nal', '--net-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Network: global level (0=standard, 1=advanced, 2=expert)')

        # ... processes statistics: PID(s) selection
        self.__oArgumentParser.add_argument(
            '-P', '--process', type=str,
            metavar='<pid>[,<pid> ...]',
            default=None,
            help='Process statistics: comma-separated list of process PIDs; \'*\' for all')

        # ... processes statistics: status
        self.__oArgumentParser.add_argument(
            '-Pu', '--proc-status', action='store_true',
            default=False,
            help='Process status (/proc/<pid>/status)')
        self.__oArgumentParser.add_argument(
            '-Pul', '--proc-status-level', type=int,
            metavar='<level>',
            default=0,
            help='Process status: level (0=standard, 1=advanced, 2=expert)')

        # ... processes statistics: statistics
        self.__oArgumentParser.add_argument(
            '-Ps', '--proc-stat', action='store_true',
            default=False,
            help='Process statistics (/proc/<pid>/stat)')
        self.__oArgumentParser.add_argument(
            '-Psl', '--proc-stat-level', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... processes statistics: I/Os
        self.__oArgumentParser.add_argument(
            '-Pi', '--proc-io', action='store_true',
            default=False,
            help='Process I/Os statistics (/proc/<pid>/io)')
        self.__oArgumentParser.add_argument(
            '-Pil', '--proc-io-level', type=int,
            metavar='<level>',
            default=0,
            help='Process I/Os statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... processes statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Pa', '--proc-all', action='store_true',
            default=False,
            help='Process statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Pal', '--proc-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: global level (0=standard, 1=advanced, 2=expert)')

        # ... virtualization statistics: guest(s) selection
        self.__oArgumentParser.add_argument(
            '-V', '--virt', type=str,
            metavar='<guest>[,<guest> ...]',
            default=None,
            help='Virtualization statistics: comma-separated list of guests (VMs); \'*\' for all')

        # ... virtualization statistics: Libvirt domain statistics
        self.__oArgumentParser.add_argument(
            '-Vs', '--virt-stat', action='store_true',
            default=False,
            help='Libvirt domain statistics (virsh domstats)')
        self.__oArgumentParser.add_argument(
            '-Vsl', '--virt-stat-level', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt domain statistics: level (0=standard, 1=advanced, 2=expert)')

        # ... virtualization statistics: ALL
        self.__oArgumentParser.add_argument(
            '-Va', '--virt-all', action='store_true',
            default=False,
            help='Virtualization statistics: all statistics')
        self.__oArgumentParser.add_argument(
            '-Val', '--virt-all-level', type=int,
            metavar='<level>',
            default=0,
            help='Virtualization statistics: global level (0=standard, 1=advanced, 2=expert)')

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
        bExitOnError = self.__oArguments.exit_on_error

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

        # ... CPU statistics
        bStats_cpu_all = self.__oArguments.cpu_all
        iStats_cpu_all_level = self.__oArguments.cpu_all_level
        bStats_cpu_info = bStats_cpu_all or self.__oArguments.cpu_info
        iLevel_cpu_info = max(iStats_cpu_all_level, self.__oArguments.cpu_info_level)
        bStats_cpu_load = bStats_cpu_all or self.__oArguments.cpu_load
        iLevel_cpu_load = iStats_cpu_all_level
        bStats_cpu_stat = bStats_cpu_all or self.__oArguments.cpu_stat
        iLevel_cpu_stat = max(iStats_cpu_all_level, self.__oArguments.cpu_stat_level)
        bDetail_cpu_stat = self.__oArguments.cpu_stat_detail

        # ... memory statistics
        bStats_mem_all = self.__oArguments.mem_all
        iStats_mem_all_level = self.__oArguments.mem_all_level
        bStats_mem_info = bStats_mem_all or self.__oArguments.mem_info
        iLevel_mem_info = max(iStats_mem_all_level, self.__oArguments.mem_info_level)
        bStats_mem_vm = bStats_mem_all or self.__oArguments.mem_vm
        iLevel_mem_vm = max(iStats_mem_all_level, self.__oArguments.mem_vm_level)

        # ... I/O statistics
        bStats_io_all = self.__oArguments.io_all
        iStats_io_all_level = self.__oArguments.io_all_level
        bStats_io_disk = bStats_io_all or self.__oArguments.io_disk
        iLevel_io_disk = max(iStats_io_all_level, self.__oArguments.io_disk_level)
        sDevice_io_disk = self.__oArguments.io_disk_device
        bStats_io_mount = bStats_io_all or self.__oArguments.io_mount
        iLevel_io_mount = max(iStats_io_all_level, self.__oArguments.io_mount_level)
        sDevice_io_mount = self.__oArguments.io_mount_device
        sMountpoint_io_mount = self.__oArguments.io_mount_mountpoint

        # ... network statistics
        bStats_net_all = self.__oArguments.net_all
        iStats_net_all_level = self.__oArguments.net_all_level
        bStats_net_dev = bStats_net_all or self.__oArguments.net_dev
        iLevel_net_dev = max(iStats_net_all_level, self.__oArguments.net_dev_level)
        sDevice_net_dev = self.__oArguments.net_dev_device
        bStats_net_tcp = bStats_net_all or self.__oArguments.net_tcp
        iLevel_net_tcp = max(iStats_net_all_level, self.__oArguments.net_tcp_level)
        bStats_net_udp = bStats_net_all or self.__oArguments.net_udp
        iLevel_net_udp = max(iStats_net_all_level, self.__oArguments.net_udp_level)

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

        # ... virtualization statistics
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
        bStats_virt_stat = bStats_virt_all or self.__oArguments.virt_stat
        iLevel_virt_stat = max(iStats_virt_all_level, self.__oArguments.virt_stat_level)


        # Signal handling
        signal.signal(signal.SIGINT, self.__signal)
        signal.signal(signal.SIGTERM, self.__signal)

        # Parse statistics

        # ... timestamp
        if bTimestamp:
            sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        # ... gather statistics
        oGUStatData_1 = GUStatData(bInterval, not bRaw, _bThrowErrors=bExitOnError)
        if bStats_cpu_info:
            oGUStatData_1.parseStat_cpu_info(iLevel_cpu_info)
        if bStats_cpu_load:
            oGUStatData_1.parseStat_cpu_load(iLevel_cpu_load)
        if bStats_cpu_stat:
            oGUStatData_1.parseStat_cpu_stat(iLevel_cpu_stat, bDetail_cpu_stat)
        if bStats_mem_info:
            oGUStatData_1.parseStat_mem_info(iLevel_mem_info)
        if bStats_mem_vm:
            oGUStatData_1.parseStat_mem_vm(iLevel_mem_vm)
        if bStats_io_disk:
            oGUStatData_1.parseStat_io_disk(iLevel_io_disk, sDevice_io_disk)
        if bStats_io_mount:
            oGUStatData_1.parseStat_io_mount(iLevel_io_mount, sDevice_io_mount, sMountpoint_io_mount)
        if bStats_net_dev:
            oGUStatData_1.parseStat_net_dev(iLevel_net_dev, sDevice_net_dev)
        if bStats_net_tcp:
            oGUStatData_1.parseStat_net_tcp(iLevel_net_tcp)
        if bStats_net_udp:
            oGUStatData_1.parseStat_net_udp(iLevel_net_udp)
        for iPid in lPids:
            if bStats_proc_status:
                oGUStatData_1.parseStat_proc_status(iLevel_proc_status, iPid)
            if bStats_proc_stat:
                oGUStatData_1.parseStat_proc_stat(iLevel_proc_stat, iPid)
            if bStats_proc_io:
                oGUStatData_1.parseStat_proc_io(iLevel_proc_io, iPid)
        for sGuest in lGuests:
            if bStats_virt_stat:
                oGUStatData_1.parseStat_virt_stat(iLevel_virt_stat, sGuest)

        # ... display statistics
        if not bInterval:
            try:
                oGUStatData_1.display(sTimestamp, sIntFormat, sFloatFormat, bZeroHide, iJustify)
            except:
                return 0
            return 0


        # Interval mode
        oGUStatData_2 = GUStatData(bInterval, not bRaw, _bThrowErrors=bExitOnError)
        oGUStatData_D = GUStatData(bInterval, not bRaw, _bThrowErrors=bExitOnError)
        iIntervalCount = 0
        while True:
            time.sleep(self.__oArguments.interval)
            iIntervalCount += 1

            # ... timestamp
            if bTimestamp:
                sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            # ... gather statistics
            if bStats_cpu_info:
                oGUStatData_2.parseStat_cpu_info(iLevel_cpu_info)
            if bStats_cpu_load:
                oGUStatData_2.parseStat_cpu_load(iLevel_cpu_load)
            if bStats_cpu_stat:
                oGUStatData_2.parseStat_cpu_stat(iLevel_cpu_stat, bDetail_cpu_stat)
            if bStats_mem_info:
                oGUStatData_2.parseStat_mem_info(iLevel_mem_info)
            if bStats_mem_vm:
                oGUStatData_2.parseStat_mem_vm(iLevel_mem_vm)
            if bStats_io_disk:
                oGUStatData_2.parseStat_io_disk(iLevel_io_disk, sDevice_io_disk)
            if bStats_io_mount:
                oGUStatData_2.parseStat_io_mount(iLevel_io_mount, sDevice_io_mount, sMountpoint_io_mount)
            if bStats_net_dev:
                oGUStatData_2.parseStat_net_dev(iLevel_net_dev, sDevice_net_dev)
            if bStats_net_tcp:
                oGUStatData_2.parseStat_net_tcp(iLevel_net_tcp)
            if bStats_net_udp:
                oGUStatData_2.parseStat_net_udp(iLevel_net_udp)
            for iPid in lPids:
                if bStats_proc_status:
                    oGUStatData_2.parseStat_proc_status(iLevel_proc_status, iPid)
                if bStats_proc_stat:
                    oGUStatData_2.parseStat_proc_stat(iLevel_proc_stat, iPid)
                if bStats_proc_io:
                    oGUStatData_2.parseStat_proc_io(iLevel_proc_io, iPid)
            for sGuest in lGuests:
                if bStats_virt_stat:
                    oGUStatData_2.parseStat_virt_stat(iLevel_virt_stat, sGuest)

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

