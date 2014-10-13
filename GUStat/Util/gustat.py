#!/usr/bin/env python
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


# Signal handlers
GUSTAT_MAIN_INTERRUPTED = False
def GUSTAT_MAIN_SIGNAL_HANDLER( _signal, _frame ):
    global GUSTAT_MAIN_INTERRUPTED
    GUSTAT_MAIN_INTERRUPTED = True


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

    def __init__( self ):
        # Fields
        self.oArgumentParser = None
        self.oArguments = None

        # Initialization
        self.__initArgumentParser()


    def __initArgumentParser( self ):
        """
        Creates the arguments parser (and help generator)
        """

        # Create argument parser
        self.oArgumentParser = AP.ArgumentParser(
            prog = sys.argv[0].split('/')[-1],
            formatter_class = AP.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent( '''\
                Refer to the Linux kernel /proc documention for details on gathered statistics:
                  man 5 proc
                 or
                  https://www.kernel.org/doc/Documentation/filesystems/proc.txt
                ''' ) )

        # ... global: output preferences
        self.oArgumentParser.add_argument(
            '-t', '--timestamp', action='store_true',
            default=False,
            help='Output: prefix output with timestamp' )
        self.oArgumentParser.add_argument(
            '-p', '--precision', type=int,
            metavar='<decimals>',
            default=-1,
            help='Output: decimal precision for float values' )
        self.oArgumentParser.add_argument(
            '-0', '--zero_hide', action='store_true',
            default=False,
            help='Output: do not show zero values' )
        self.oArgumentParser.add_argument(
            '-j', '--justify', type=int,
            metavar='<width>',
            default=-1,
            help='Output: justify output width, in characters (0=autodetect)' )
        self.oArgumentParser.add_argument(
            '-s', '--thousands', action='store_true',
            default=False,
            help='Output: display thousands separator (justify mode only)' )
        self.oArgumentParser.add_argument(
            '-o', '--top', action='store_true',
            default=False,
            help='Output: always start output at top of screen' )

        # ... global: interval mode
        self.oArgumentParser.add_argument(
            '-i', '--interval', type=int,
            metavar='<seconds>',
            default=0,
            help='Interval: statistics gathering interval, in seconds [s]' )
        self.oArgumentParser.add_argument(
            '-c', '--continuous', action='store_true',
            default=False,
            help='Interval: continuous statistics gathering' )
        self.oArgumentParser.add_argument(
            '-d', '--differential', action='store_true',
            default=False,
            help='Interval: display differences relative to start of sampling rather than last interval' )
        self.oArgumentParser.add_argument(
            '-r', '--raw', action='store_true',
            default=False,
            help='Interval: display raw differences rather than rates' )

        # ... system stats: CPU information
        self.oArgumentParser.add_argument(
            '-Sc', '--sys_cpu', action='store_true',
            default=False,
            help='System CPU information (/proc/cpuinfo)' )

        # ... system stats: load average
        self.oArgumentParser.add_argument(
            '-Sl', '--sys_load', action='store_true',
            default=False,
            help='System load average (/proc/loadavg)' )

        # ... system stats: misc. kernel statistics
        self.oArgumentParser.add_argument(
            '-Ss', '--sys_stat', action='store_true',
            default=False,
            help='System kernel statistics (/proc/stat)' )
        self.oArgumentParser.add_argument(
            '-Ssl', '--sys_stat_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System kernel statistics: level (0=standard, 1=advanced, 2=expert)' )
        self.oArgumentParser.add_argument(
            '-Ssd', '--sys_stat_dtl', action='store_true',
            default=False,
            help='System kernel statistics: show detailed (CPU) statistics' )

        # ... system stats: memory information
        self.oArgumentParser.add_argument(
            '-Sm', '--sys_mem', action='store_true',
            default=False,
            help='System memory information (/proc/meminfo)' )
        self.oArgumentParser.add_argument(
            '-Sml', '--sys_mem_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System memory information: level (0=standard, 1=advanced, 2=expert)' )

        # ... system stats: virtual memory statistics
        self.oArgumentParser.add_argument(
            '-Sv', '--sys_vm', action='store_true',
            default=False,
            help='System virtual memory statistics (/proc/vmstat)' )
        self.oArgumentParser.add_argument(
            '-Svl', '--sys_vm_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System virtual memory statistics: level (0=standard, 1=advanced, 2=expert)' )

        # ... system stats: disks statistics
        self.oArgumentParser.add_argument(
            '-Sd', '--sys_dsks', action='store_true',
            default=False,
            help='System disks statistics (/proc/diskstats)' )
        self.oArgumentParser.add_argument(
            '-Sdl', '--sys_dsks_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System disks statistics: level (0=standard, 1=advanced, 2=expert)' )
        self.oArgumentParser.add_argument(
            '-Sdd', '--sys_dsks_dev', type=str,
            metavar='<level>',
            default=None,
            help='System disks statistics: device name' )
        self.oArgumentParser.add_argument(
            '-Sdp', '--sys_dsks_pfx', action='store_true',
            default=False,
            help='System disks statistics: match device name prefix' )

        # ... system stats: mounts statistics
        self.oArgumentParser.add_argument(
            '-St', '--sys_mnts', action='store_true',
            default=False,
            help='System mounts statistics (/proc/self/mountstats)' )
        self.oArgumentParser.add_argument(
            '-Stl', '--sys_mnts_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System mounts statistics: level (0=standard, 1=advanced, 2=expert)' )
        self.oArgumentParser.add_argument(
            '-Std', '--sys_mnts_dev', type=str,
            metavar='<device>',
            default=None,
            help='System mounts statistics: device name' )
        self.oArgumentParser.add_argument(
            '-Stp', '--sys_mnts_pfx', action='store_true',
            default=False,
            help='System mounts statistics: match device name prefix' )

        # ... system stats: network statistics
        self.oArgumentParser.add_argument(
            '-Sn', '--sys_net', action='store_true',
            default=False,
            help='System network statistics (/proc/net/dev)' )
        self.oArgumentParser.add_argument(
            '-Snl', '--sys_net_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System network statistics: level (0=standard, 1=advanced, 2=expert)' )
        self.oArgumentParser.add_argument(
            '-Snd', '--sys_net_dev', type=str,
            metavar='<device>',
            default=None,
            help='System network statistics: device name' )
        self.oArgumentParser.add_argument(
            '-Snp', '--sys_net_pfx', action='store_true',
            default=False,
            help='System network statistics: match device name prefix' )

        # ... system stats: all
        self.oArgumentParser.add_argument(
            '-Sa', '--sys_all', action='store_true',
            default=False,
            help='System statistics: all statistics' )
        self.oArgumentParser.add_argument(
            '-Sal', '--sys_all_lvl', type=int,
            metavar='<level>',
            default=0,
            help='System statistics: global level (0=standard, 1=advanced, 2=expert)' )

        # ... process stats: PIDs
        self.oArgumentParser.add_argument(
            '-P', '--process', type=str,
            metavar='<pid>[,<pid> ...]',
            default=None,
            help='Process statistics: comma-separated list of process PIDs' )

        # ... process stats: status
        self.oArgumentParser.add_argument(
            '-Pu', '--proc_status', action='store_true',
            default=False,
            help='Process status (/proc/<pid>/status)' )
        self.oArgumentParser.add_argument(
            '-Pul', '--proc_status_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process status: level (0=standard, 1=advanced, 2=expert)' )

        # ... process stats: statistics
        self.oArgumentParser.add_argument(
            '-Ps', '--proc_stat', action='store_true',
            default=False,
            help='Process statistics (/proc/<pid>/stat)' )
        self.oArgumentParser.add_argument(
            '-Psl', '--proc_stat_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: level (0=standard, 1=advanced, 2=expert)' )

        # ... process stats: I/Os
        self.oArgumentParser.add_argument(
            '-Pi', '--proc_io', action='store_true',
            default=False,
            help='Process I/Os statistics (/proc/<pid>/io)' )
        self.oArgumentParser.add_argument(
            '-Pil', '--proc_io_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process I/Os statistics: level (0=standard, 1=advanced, 2=expert)' )

        # ... process stats: all
        self.oArgumentParser.add_argument(
            '-Pa', '--proc_all', action='store_true',
            default=False,
            help='Process statistics: all statistics' )
        self.oArgumentParser.add_argument(
            '-Pal', '--proc_all_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Process statistics: global level (0=standard, 1=advanced, 2=expert)' )

        # ... Libvirt stats: VMs
        self.oArgumentParser.add_argument(
            '-V', '--virt', type=str,
            metavar='<vm>[,<vm> ...]',
            default=None,
            help='Libvirt statistics: comma-separated list of guests (VMs)' )

        # ... Libvirt stats: Qemu block devices statistics
        self.oArgumentParser.add_argument(
            '-Vb', '--virt_blks', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics (info blockstats)' )
        self.oArgumentParser.add_argument(
            '-Vbl', '--virt_blks_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt/Qemu block devices statistics: level (0=standard, 1=advanced, 2=expert)' )
        self.oArgumentParser.add_argument(
            '-Vbd', '--virt_blks_dev', type=str,
            metavar='<device>',
            default=None,
            help='Libvirt/Qemu block devices statistics: device name' )
        self.oArgumentParser.add_argument(
            '-Vbp', '--virt_blks_pfx', action='store_true',
            default=False,
            help='Libvirt/Qemu block devices statistics: match device name prefix' )

        # ... Libvirt stats: all
        self.oArgumentParser.add_argument(
            '-Va', '--virt_all', action='store_true',
            default=False,
            help='Libvirt statistics: all statistics' )
        self.oArgumentParser.add_argument(
            '-Val', '--virt_all_lvl', type=int,
            metavar='<level>',
            default=0,
            help='Libvirt statistics: global level (0=standard, 1=advanced, 2=expert)' )

        # ... other
        self.oArgumentParser.add_argument(
            '-v', '--version', action='version',
            version=( 'GUStat - %s - Cedric Dufour <http://cedric.dufour.name>\n' % GUSTAT_VERSION ) )


    def __initArguments( self, _aArguments = None ):
        """
        Parses the command-line arguments; returns a non-zero exit code in case of failure.
        """

        # Parse arguments
        if _aArguments is None:
            _aArguments = sys.argv
        try:
            self.oArguments = self.oArgumentParser.parse_args()
        except Exception, e:
            self.oArguments = None
            sys.stderr.write( 'ERROR: Failed to parse arguments; %s\n' % str(e) )
            return 1

        return 0


    #------------------------------------------------------------------------------
    # METHODS
    #------------------------------------------------------------------------------

    #
    # Helpers
    #

    # Shamelessly copied from http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    def __getTerminalSize( self ):
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

    def execute( self ):
        """
        Executes the Global Statistics parser; returns a non-zero exit code in case of failure.
        """

        # Parse arguments
        __iReturn = self.__initArguments()
        if __iReturn:
            return __iReturn

        # ... output formatting
        __bTimestamp = self.oArguments.timestamp
        __sTimestamp = None
        __sIntFormat = '{:}'
        __sFloatFormat = '{:}'
        if self.oArguments.precision >= 0:
            __sFloatFormat = __sFloatFormat.replace( ':', ':.'+str( self.oArguments.precision )+'f' )
        __bZeroHide = self.oArguments.zero_hide
        __iJustify = self.oArguments.justify
        __bTop = self.oArguments.top
        if __bTop and __iJustify < 0:
            __iJustify = 0
        if __iJustify == 0:
            ( __iWidth, __iHeight ) = self.__getTerminalSize()
            __iJustify = __iWidth
        if __iJustify < 40:
            __bTop = False
            __iJustify = -1
        if __iJustify > 0 and self.oArguments.thousands:
            __sIntFormat = __sIntFormat.replace( ':', ':,' )
            __sFloatFormat = __sFloatFormat.replace( ':', ':,' )
        if __sIntFormat == '{:}':
            __sIntFormat = None
        if __sFloatFormat == '{:}':
            __sFloatFormat = None

        # ... interval mode
        __bInterval = False
        __bContinuous = False
        __bDifferential = False
        __bRaw = False
        if self.oArguments.interval > 0:
            __bInterval = True
            __bContinuous = self.oArguments.continuous
            __bDifferential = self.oArguments.differential
            __bRaw = self.oArguments.raw

        # ... system statistics
        __bStats_sys_all = self.oArguments.sys_all
        __iStats_sys_all_lvl = self.oArguments.sys_all_lvl
        __bStats_sys_cpu = __bStats_sys_all or self.oArguments.sys_cpu
        __iLevel_sys_cpu = __iStats_sys_all_lvl
        __bStats_sys_load = __bStats_sys_all or self.oArguments.sys_load
        __iLevel_sys_load = __iStats_sys_all_lvl
        __bStats_sys_stat = __bStats_sys_all or self.oArguments.sys_stat
        __iLevel_sys_stat = max( __iStats_sys_all_lvl, self.oArguments.sys_stat_lvl )
        __bDetail_sys_stat = self.oArguments.sys_stat_dtl
        __bStats_sys_mem = __bStats_sys_all or self.oArguments.sys_mem
        __iLevel_sys_mem = max( __iStats_sys_all_lvl, self.oArguments.sys_mem_lvl )
        __bStats_sys_vm = __bStats_sys_all or self.oArguments.sys_vm
        __iLevel_sys_vm = max( __iStats_sys_all_lvl, self.oArguments.sys_vm_lvl )
        __bStats_sys_dsks = __bStats_sys_all or self.oArguments.sys_dsks
        __iLevel_sys_dsks = max( __iStats_sys_all_lvl, self.oArguments.sys_dsks_lvl )
        __sDevice_sys_dsks = self.oArguments.sys_dsks_dev
        __bPrefix_sys_dsks = self.oArguments.sys_dsks_pfx
        __bStats_sys_mnts = __bStats_sys_all or self.oArguments.sys_mnts
        __iLevel_sys_mnts = max( __iStats_sys_all_lvl, self.oArguments.sys_mnts_lvl )
        __sDevice_sys_mnts = self.oArguments.sys_mnts_dev
        __bPrefix_sys_mnts = self.oArguments.sys_mnts_pfx
        __bStats_sys_net = __bStats_sys_all or self.oArguments.sys_net
        __iLevel_sys_net = max( __iStats_sys_all_lvl, self.oArguments.sys_net_lvl )
        __sDevice_sys_net = self.oArguments.sys_net_dev
        __bPrefix_sys_net = self.oArguments.sys_net_pfx

        # ... processes statistics
        __lPids = list()
        if self.oArguments.process is not None:
            __lPids = self.oArguments.process.strip(',').split(',')
            try:
                map( int, __lPids )
            except:
                sys.stderr.write( 'ERROR: Invalid process PIDs; %s\n' % self.oArguments.process )
                return 1
        __bStats_proc_all = self.oArguments.proc_all
        __iStats_proc_all_lvl = self.oArguments.proc_all_lvl
        __bStats_proc_status = __bStats_proc_all or self.oArguments.proc_status
        __iLevel_proc_status = max( __iStats_proc_all_lvl, self.oArguments.proc_status_lvl )
        __bStats_proc_stat = __bStats_proc_all or self.oArguments.proc_stat
        __iLevel_proc_stat = max( __iStats_proc_all_lvl, self.oArguments.proc_stat_lvl )
        __bStats_proc_io = __bStats_proc_all or self.oArguments.proc_io
        __iLevel_proc_io = max( __iStats_proc_all_lvl, self.oArguments.proc_io_lvl )

        # ... libvirt statistics
        __lGuests = list()
        if self.oArguments.virt is not None:
            __lGuests = self.oArguments.virt.strip(',').split(',')
        __bStats_virt_all = self.oArguments.virt_all
        __iStats_virt_all_lvl = self.oArguments.virt_all_lvl
        __bStats_virt_blks = __bStats_virt_all or self.oArguments.virt_blks
        __iLevel_virt_blks = max( __iStats_virt_all_lvl, self.oArguments.virt_blks_lvl )
        __sDevice_virt_blks = self.oArguments.virt_blks_dev
        __bPrefix_virt_blks = self.oArguments.virt_blks_pfx


        # Signal handling
        signal.signal( signal.SIGINT, GUSTAT_MAIN_SIGNAL_HANDLER )

        # Parse statistics

        # ... timestamp
        if __bTimestamp:
            __sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        # ... gather statistics
        __oGUStatData_1 = GUStatData( __bInterval, not __bRaw )
        if __bStats_sys_cpu:
            __oGUStatData_1.parseStat_sys_cpu( __iLevel_sys_cpu )
        if __bStats_sys_load:
            __oGUStatData_1.parseStat_sys_load( __iLevel_sys_load )
        if __bStats_sys_stat:
            __oGUStatData_1.parseStat_sys_stat( __iLevel_sys_stat, __bDetail_sys_stat )
        if __bStats_sys_mem:
            __oGUStatData_1.parseStat_sys_mem( __iLevel_sys_mem )
        if __bStats_sys_vm:
            __oGUStatData_1.parseStat_sys_vm( __iLevel_sys_vm )
        if __bStats_sys_dsks:
            __oGUStatData_1.parseStat_sys_dsks( __iLevel_sys_dsks, __sDevice_sys_dsks, __bPrefix_sys_dsks )
        if __bStats_sys_mnts:
            __oGUStatData_1.parseStat_sys_mnts( __iLevel_sys_mnts, __sDevice_sys_mnts, __bPrefix_sys_mnts )
        if __bStats_sys_net:
            __oGUStatData_1.parseStat_sys_net( __iLevel_sys_net, __sDevice_sys_net, __bPrefix_sys_net )
        for __iPid in __lPids:
            if __bStats_proc_status:
                __oGUStatData_1.parseStat_proc_status( __iLevel_proc_status, __iPid )
            if __bStats_proc_stat:
                __oGUStatData_1.parseStat_proc_stat( __iLevel_proc_stat, __iPid )
            if __bStats_proc_io:
                __oGUStatData_1.parseStat_proc_io( __iLevel_proc_io, __iPid )
        for __sGuest in __lGuests:
            if __bStats_virt_blks:
                __oGUStatData_1.parseStat_virt_blks( __iLevel_virt_blks, __sGuest, __sDevice_virt_blks, __bPrefix_virt_blks )

        # ... display statistics
        if not __bInterval:
            try:
                __oGUStatData_1.display( __sTimestamp, __sIntFormat, __sFloatFormat, __bZeroHide, __iJustify )
            except:
                return 0
            return 0


        # Interval mode
        __oGUStatData_2 = GUStatData( __bInterval, not __bRaw )
        __oGUStatData_D = GUStatData( __bInterval, not __bRaw )
        __iIntervalCount = 0
        while True:
            time.sleep( self.oArguments.interval )
            __iIntervalCount += 1

            # ... timestamp
            if __bTimestamp:
                __sTimestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

            # ... gather statistics
            if __bStats_sys_cpu:
                __oGUStatData_2.parseStat_sys_cpu( __iLevel_sys_cpu )
            if __bStats_sys_load:
                __oGUStatData_2.parseStat_sys_load( __iLevel_sys_load )
            if __bStats_sys_stat:
                __oGUStatData_2.parseStat_sys_stat( __iLevel_sys_stat, __bDetail_sys_stat )
            if __bStats_sys_mem:
                __oGUStatData_2.parseStat_sys_mem( __iLevel_sys_mem )
            if __bStats_sys_vm:
                __oGUStatData_2.parseStat_sys_vm( __iLevel_sys_vm )
            if __bStats_sys_dsks:
                __oGUStatData_2.parseStat_sys_dsks( __iLevel_sys_dsks, __sDevice_sys_dsks, __bPrefix_sys_dsks )
            if __bStats_sys_mnts:
                __oGUStatData_2.parseStat_sys_mnts( __iLevel_sys_mnts, __sDevice_sys_mnts, __bPrefix_sys_mnts )
            if __bStats_sys_net:
                __oGUStatData_2.parseStat_sys_net( __iLevel_sys_net, __sDevice_sys_net, __bPrefix_sys_net )
            for __iPid in __lPids:
                if __bStats_proc_status:
                    __oGUStatData_2.parseStat_proc_status( __iLevel_proc_status, __iPid )
                if __bStats_proc_stat:
                    __oGUStatData_2.parseStat_proc_stat( __iLevel_proc_stat, __iPid )
                if __bStats_proc_io:
                    __oGUStatData_2.parseStat_proc_io( __iLevel_proc_io, __iPid )
            for __sGuest in __lGuests:
                if __bStats_virt_blks:
                    __oGUStatData_2.parseStat_virt_blks( __iLevel_virt_blks, __sGuest, __sDevice_virt_blks, __bPrefix_virt_blks )

            # ... compute differences
            for __sKey in __oGUStatData_1.dStats.iterkeys():
                if __sKey not in __oGUStatData_2.dStats.iterkeys():
                    continue
                __oGUStatData_D.dStats[__sKey] = \
                    copy.deepcopy( __oGUStatData_2.dStats[__sKey] )
                __oGUStatData_D.dStats[__sKey]['value'] = float(
                    __oGUStatData_2.dStats[__sKey]['value'] -
                    __oGUStatData_1.dStats[__sKey]['value'] )
                if not __bRaw:
                    __oGUStatData_D.dStats[__sKey]['unit'] += '/s'
                    __oGUStatData_D.dStats[__sKey]['value'] /= self.oArguments.interval
                    if __bDifferential:
                        __oGUStatData_D.dStats[__sKey]['value'] /= __iIntervalCount
                if not __bDifferential:
                    __oGUStatData_1.dStats[__sKey]['value'] = \
                        __oGUStatData_2.dStats[__sKey]['value']

            # ... display differences
            try:
                if __bTop:
                    #sys.stdout.write( chr(27)+'[2J' )
                    sys.stdout.write( '\x1b[2J\x1b[H' )
                    if __sTimestamp is not None:
                        sys.stdout.write( '# GUStat - %s\n' % __sTimestamp )
                    else:
                        sys.stdout.write( '# GUStat\n' )
                    __oGUStatData_D.display( None, __sIntFormat, __sFloatFormat, __bZeroHide, __iJustify )
                else:
                    __oGUStatData_D.display( __sTimestamp, __sIntFormat, __sFloatFormat, __bZeroHide, __iJustify )
            except:
                break

            # ... continue
            if not __bContinuous or GUSTAT_MAIN_INTERRUPTED:
                break

        return 0

