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
import re
import signal
from subprocess import check_output
import sys
import textwrap
import time


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class GUInfluxMain:
    """
    Global Statistics Influx Line Protocol Generator
    """

    #------------------------------------------------------------------------------
    # CONSTRUCTORS / DESTRUCTOR
    #------------------------------------------------------------------------------

    def __init__(self):
        # Fields
        self.__oArgumentParser = None
        self.__oArguments = None

        # Initialization
        self.__initArgumentParser()

        # System configuration
        self.__sHostname = 'localhost'
        self.__iClockTicks = 100
        self.__iPageSize = 4096
        try:
            # ... CPU ticks per clock-cycle/second
            lCommand = ['hostname']
            self.__sHostname = check_output(lCommand).decode(sys.stdout.encoding).strip()
            # ... CPU ticks per clock-cycle/second
            lCommand = ['getconf', 'CLK_TCK']
            self.__iClockTicks = int(check_output(lCommand).decode(sys.stdout.encoding).strip())
            # ... memory page size
            lCommand = ['getconf', 'PAGE_SIZE']
            self.__iPageSize = int(check_output(lCommand).decode(sys.stdout.encoding).strip())
        except:
            sys.stderr.write('ERROR: System configuration retrieval command failed; %s\n' % ' '.join(lCommand))

        # Measurements
        self.__sTimestamp = str(int(time.time()*1000000000))
        self.__dMeasurements = dict()

    def __initArgumentParser(self):
        """
        Creates the arguments parser (and help generator)
        """

        # Create argument parser
        self.__oArgumentParser = AP.ArgumentParser(sys.argv[0].split('/')[-1])

        # ... global: output preferences
        self.__oArgumentParser.add_argument(
            '-t', '--timestamp', action='store_true',
            default=False,
            help='Output: suffix output with timestamp')

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
            help='Mounts statistics: level (0=standard, 1=advanced, 2=expert, 3=guru)')
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
        self.__oArgumentParser.add_argument(
            '-Pun', '--proc-status-name', action='store_true',
            default=False,
            help='Process status: show user/group name instead of UID/GID')

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
        self.__oArgumentParser.add_argument(
            '-Pau', '--proc-all-uid', type=str,
            metavar='<uid>|re/<uid>/',
            default=None,
            help='Process statistics: filter by UID')
        self.__oArgumentParser.add_argument(
            '-Pag', '--proc-all-gid', type=str,
            metavar='<gid>|re/<gid>/',
            default=None,
            help='Process statistics: filter by GID')

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

    def __addMeasurements(self, _lsMeasurements):
        if not isinstance(_lsMeasurements, list):
            _lsMeasurements = list(_lsMeasurements)
        for sMeasurement in set(_lsMeasurements) - set(self.__dMeasurements.keys()):
            self.__dMeasurements[sMeasurement] = dict()

    def __storeMeasurement(self, _sMeasurement, _sObject, _dField):
        try:
            dMeasurement = self.__dMeasurements[_sMeasurement]
        except KeyError as e:
            return

        # Object
        if _sObject not in dMeasurement.keys():
            dMeasurement[_sObject] = {'tags': dict(), 'fields': dict()}

        # Units
        if _dField['unit'] == 'ticks':
            _dField['value'] /= self.__iClockTicks
            _dField['unit'] = 'seconds'
        elif _dField['unit'] == 'pages':
            _dField['value'] *= self.__iPageSize
            _dField['unit'] = 'bytes'

        # Metric
        if _dField['category'] != '-':
            sMetric = _dField['category']+'_'+_dField['metric']
        else:
            sMetric = _dField['metric']
        if not _dField['unit'] in ['id', 'name'] and not sMetric.endswith('_'+_dField['unit']):
            sMetric += '_'+_dField['unit']

        # Value
        mValue = _dField['value']

        # Store
        if _dField['unit'] in ['id', 'name']:
            dMeasurement[_sObject]['tags'][sMetric] = str(mValue)
        elif isinstance(mValue, str):
            dMeasurement[_sObject]['fields'][sMetric] = '"%s"' % mValue.replace('"', '\"')
        elif isinstance(mValue, int):
            dMeasurement[_sObject]['fields'][sMetric] = str(mValue)+'i'
        elif isinstance(mValue, float):
            dMeasurement[_sObject]['fields'][sMetric] = str(mValue)

    def __dropMeasurement(self, _sMeasurement, _sObject = None):
        if _sObject is None:
            self.__dMeasurements.pop(_sMeasurement, None)
        else:
            try:
                dMeasurement = self.__dMeasurements[_sMeasurement]
            except KeyError as e:
                return
            dMeasurement.pop(_sObject, None)

    def __displayMeasurements(self, _bTimestamp):
        # REF: https://docs.influxdata.com/influxdb/v1.5/write_protocols/line_protocol_reference/
        dSpecialCharacters = str.maketrans({ ',': '\,', '=': '\=', ' ': '\ ', '"': '\"' })
        for sMeasurement in sorted(self.__dMeasurements.keys()):
            dMeasurement = self.__dMeasurements[sMeasurement]
            for sObject in dMeasurement.keys():
                if not len(dMeasurement[sObject]['fields']):
                    continue
                # Measurement
                sOutput = sMeasurement

                # Tags
                dTags = dMeasurement[sObject]['tags']
                dTags['host'] = self.__sHostname
                if sObject != '-':
                    iTag = 0
                    for sTag in sObject.split(','):
                        lTag = sTag.split('=', 1)
                        if len(lTag) < 2:
                            dTags['object%d' % iTag] = lTag[0]
                        else:
                            dTags[lTag[0]] = lTag[1]
                        iTag += 1
                for sTag in sorted(dTags.keys()):
                    sOutput += ',%s=%s' % (sTag.translate(dSpecialCharacters), dTags[sTag].translate(dSpecialCharacters))

                # Fields
                sOutput += ' '
                sSeparator = ''
                dFields = dMeasurement[sObject]['fields']
                for sField in sorted(dFields.keys()):
                    sOutput += sSeparator
                    sOutput += '%s=%s' % (sField.translate(dSpecialCharacters), dFields[sField])
                    sSeparator = ','

                # Timestamp
                if _bTimestamp:
                    sOutput += ' %s' % self.__sTimestamp

                # Done
                sys.stdout.write('%s\n' % sOutput)

    #
    # Main
    #

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
        bNameId_proc_status = self.__oArguments.proc_status_name
        bStats_proc_stat = bStats_proc_all or self.__oArguments.proc_stat
        iLevel_proc_stat = max(iStats_proc_all_level, self.__oArguments.proc_stat_level)
        bStats_proc_io = bStats_proc_all or self.__oArguments.proc_io
        iLevel_proc_io = max(iStats_proc_all_level, self.__oArguments.proc_io_level)
        sUid_proc_all = self.__oArguments.proc_all_uid
        sGid_proc_all = self.__oArguments.proc_all_gid

        # ... virtualization statistics
        lGuests = list()
        if self.__oArguments.virt is not None:
            if self.__oArguments.virt == '*':
                lCommand = ['virsh', '--quiet', 'list', '--name']
                try:
                    lGuests = sorted(check_output(lCommand).decode(sys.stdout.encoding).splitlines())
                except:
                    sys.stderr.write('ERROR: Command failed; %s\n' % ' '.join(lCommand))
            else:
                lGuests = self.__oArguments.virt.strip(',').split(',')
        bStats_virt_all = self.__oArguments.virt_all
        iStats_virt_all_level = self.__oArguments.virt_all_level
        bStats_virt_stat = bStats_virt_all or self.__oArguments.virt_stat
        iLevel_virt_stat = max(iStats_virt_all_level, self.__oArguments.virt_stat_level)


        # Parse and display statistics

        # ... CPU statistics
        if bStats_cpu_info or bStats_cpu_load or bStats_cpu_stat:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_cpu_info(iLevel_cpu_info if bStats_cpu_info else 0)
            if bStats_cpu_load:
                oGUStatData.parseStat_cpu_load(iLevel_cpu_load)
            if bStats_cpu_stat:
                oGUStatData.parseStat_cpu_stat(iLevel_cpu_stat, bDetail_cpu_stat)
            # ... to Influx
            self.__addMeasurements(['cpu_load', 'cpu_info', 'cpu_detail'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement_in, sMetric, sObject) = sKey.split(',', 2)
                sMeasurement_out = sMeasurement_in
                dField = oGUStatData.dStats[sKey]
                if sMeasurement_in == 'cpu_load':
                    sObject = 'type=%s' % sObject
                elif sMeasurement_in == 'cpu_info':
                    if sObject == 'cpu':
                        sMeasurement_out = 'cpu_info'
                        sObject = '-'
                    else:
                        sMeasurement_out = 'cpu_detail'
                        sObject = 'cpu=%s' % sObject
                elif sMeasurement_in == 'cpu_stat':
                    if sObject == 'normalized':
                        continue
                    elif sObject.startswith('cpu'):
                        sMeasurement_out = 'cpu_detail'
                        sObject = 'cpu=%s' % sObject
                    else:
                        sMeasurement_out = 'cpu_info'
                        sObject = '-'
                else:
                    continue
                dField['category'] = '-'
                self.__storeMeasurement(sMeasurement_out, sObject, dField)

        # ... memory statistics
        if bStats_mem_info:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_mem_info(iLevel_mem_info)
            # ... to Influx
            self.__addMeasurements(['mem_info'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                dField = oGUStatData.dStats[sKey]
                dField['category'] = '-'
                self.__storeMeasurement(sMeasurement, sObject, dField)

        # ... virtual memory statistics
        if bStats_mem_vm:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_mem_vm(iLevel_mem_vm)
            # ... to Influx
            self.__addMeasurements(['mem_vm'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                dField = oGUStatData.dStats[sKey]
                dField['category'] = '-'
                self.__storeMeasurement(sMeasurement, sObject, dField)

        # ... disks statistics
        if bStats_io_disk:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_io_disk(iLevel_io_disk, sDevice_io_disk)
            # ... to Influx
            self.__addMeasurements(['io_disk'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                sObject = 'device=%s' % sObject
                dField = oGUStatData.dStats[sKey]
                dField['category'] = '-'
                self.__storeMeasurement(sMeasurement, sObject, dField)

        # ... mounts statistics
        if bStats_io_mount:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_io_mount(iLevel_io_mount, sDevice_io_mount, sMountpoint_io_mount)
            # ... to Influx
            self.__addMeasurements(['io_mount_nfs'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                sObject = 'server=%s,path=%s,mountpoint=%s' % tuple(sObject.split(':', 2))
                dField = oGUStatData.dStats[sKey]
                if dField['category'] == 'io(nfs_events)':
                    dField['category'] = 'event'
                elif dField['category'] == 'io(nfs_bytes)':
                    dField['category'] = 'io'
                elif dField['category'] == 'io(nfs_rpc)':
                    dField['category'] = 'rpc'
                else:
                    dField['category'] = '-'
                self.__storeMeasurement(sMeasurement, sObject, dField)

        # ... network statistics
        if bStats_net_dev:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            oGUStatData.parseStat_net_dev(iLevel_net_dev, sDevice_net_dev)
            # ... to Influx
            self.__addMeasurements(['net_dev'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                sObject = 'device=%s' % sObject
                dField = oGUStatData.dStats[sKey]
                dField['category'] = '-'
                self.__storeMeasurement(sMeasurement, sObject, dField)

        # ... network statistics (cont'd)
        if bStats_net_tcp or bStats_net_udp:
            # ... gather
            oGUStatData = GUStatData(_bThrowErrors=True)
            if bStats_net_tcp:
                oGUStatData.parseStat_net_tcp(iLevel_net_tcp)
            if bStats_net_udp:
                oGUStatData.parseStat_net_udp(iLevel_net_udp)
            # ... to Influx
            self.__addMeasurements(['net_conn'])
            for sKey in sorted(oGUStatData.dStats.keys()):
                (sMeasurement_in, sMetric, sObject) = sKey.split(',', 2)
                dField = oGUStatData.dStats[sKey]
                dField['category'] = '-'
                self.__storeMeasurement('net_conn', sObject, dField)

        # ... processes statistics
        if bStats_proc_status or bStats_proc_stat or bStats_proc_io:
            reUid_proc_all = None
            if sUid_proc_all is not None and sUid_proc_all.startswith('re/') and sUid_proc_all.endswith('/'):
                try:
                    reUid_proc_all = re.compile(sUid_proc_all[3:-1])
                except:
                    sys.stderr.write('ERROR: Invalid regular expression; %s\n' % sUid_proc_all)
                    return 1
            reGid_proc_all = None
            if sGid_proc_all is not None and sGid_proc_all.startswith('re/') and sGid_proc_all.endswith('/'):
                try:
                    reGid_proc_all = re.compile(sGid_proc_all[3:-1])
                except:
                    sys.stderr.write('ERROR: Invalid regular expression; %s\n' % sGid_proc_all)
                    return 1
            for sPid in lPids:
                sGid = None
                sUid = None
                # ... gather
                oGUStatData = GUStatData(_bThrowErrors=True)
                try:
                    oGUStatData.parseStat_proc_status(iLevel_proc_status if bStats_proc_status else 0, sPid, bNameId_proc_status)
                    if bStats_proc_stat:
                        oGUStatData.parseStat_proc_stat(iLevel_proc_stat, sPid)
                    if bStats_proc_io:
                        oGUStatData.parseStat_proc_io(iLevel_proc_io, sPid)
                except RuntimeError:
                    continue
                # ... to Influx
                self.__addMeasurements(['proc_stat'])
                sObject_out = 'pid=%s' % sPid
                for sKey in sorted(oGUStatData.dStats.keys()):
                    (sMeasurement, sMetric, sObject) = sKey.split(',', 2)
                    dField = oGUStatData.dStats[sKey]
                    if sMeasurement == 'proc_status':
                        if sMetric in ('user:gid_effective', 'user:gid_saved', 'user:uid_effective', 'user:uid_saved'):
                            continue
                        elif sMetric == 'user:gid_real':
                            sGid = str(dField['value'])
                        elif sMetric == 'user:uid_real':
                            sUid = str(dField['value'])
                    elif sMeasurement == 'proc_stat':
                        if sMetric in ('mem:rss', 'mem:vsize', 'proc:command', 'proc:threads'):
                            continue
                    elif sMeasurement == 'proc_io':
                        pass
                    else:
                        continue
                    if dField['category'] == 'proc':
                        dField['category'] = '-'
                    self.__storeMeasurement('proc_stat', sObject_out, dField)
                # ... filter
                if reUid_proc_all is not None:
                    if not reUid_proc_all.search(sUid):
                        self.__dropMeasurement('proc_stat', sObject_out)
                elif sUid_proc_all is not None:
                    if sUid_proc_all != sUid:
                        self.__dropMeasurement('proc_stat', sObject_out)
                if reGid_proc_all is not None:
                    if not reGid_proc_all.search(sGid):
                        self.__dropMeasurement('proc_stat', sObject_out)
                elif sGid_proc_all is not None:
                    if sGid_proc_all != sGid:
                        self.__dropMeasurement('proc_stat', sObject_out)

        # ... virtualization statistics
        if bStats_virt_stat:
            for sGuest in lGuests:
                # ... gather
                oGUStatData = GUStatData(_bThrowErrors=True)
                try:
                    oGUStatData.parseStat_virt_stat(iLevel_virt_stat, sGuest)
                except RuntimeError:
                    continue
                # ... to Influx
                self.__addMeasurements(['virt_cpu', 'virt_mem', 'virt_io', 'virt_net'])
                for sKey in sorted(oGUStatData.dStats.keys()):
                    (sMeasurement_in, sMetric, sObject) = sKey.split(',', 2)
                    dField = oGUStatData.dStats[sKey]
                    if sMetric.startswith('cpu:'):
                        sMeasurement_out = 'virt_cpu'
                        sObject = 'guest=%s' % sObject
                    elif sMetric.startswith('mem:'):
                        sMeasurement_out = 'virt_mem'
                        sObject = 'guest=%s' % sObject
                    elif sMetric.startswith('io:'):
                        sMeasurement_out = 'virt_io'
                        sObject = 'guest=%s,devid=%s' % tuple(sObject.split(':', 1))
                    elif sMetric.startswith('net:'):
                        sMeasurement_out = 'virt_net'
                        sObject = 'guest=%s,devid=%s' % tuple(sObject.split(':', 1))
                    else:
                        continue
                    dField['category'] = '-'
                    self.__storeMeasurement(sMeasurement_out, sObject, dField)

        # Display
        self.__displayMeasurements(bTimestamp)

        return 0

