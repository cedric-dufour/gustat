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
import re
import subprocess as SP
import sys


#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------

# /proc/cpuinfo fields
GUSTAT_PREFIX_SYS_CPU = 'sys_cpu'
GUSTAT_FIELDS_SYS_CPU = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'count': [ 'cpu', 'count', 'cpus', None, 'int', False, False, 0 ],
    'cpu mhz': [ 'cpu', 'clock', 'herz', 1000000.0, 'int', False, False, 1 ],
    'model name': [ 'cpu', 'clock_design', 'herz', 1.0, 'int', False, False, 2 ],
}

# /proc/loadavg fields
GUSTAT_PREFIX_SYS_LOAD = 'sys_load'
GUSTAT_FIELDS_SYS_LOAD = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'field0': [ 'sys', '01min', 'load', None, 'float', False, False, 0 ],
    'field1': [ 'sys', '05min', 'load', None, 'float', False, False, 0 ],
    'field2': [ 'sys', '15min', 'load', None, 'float', False, False, 0 ],
}

# /proc/stat fields
GUSTAT_PREFIX_SYS_STAT = 'sys_stat'
GUSTAT_FIELDS_SYS_STAT = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'cpu_field1': [ 'cpu', 'user', 'ticks', None, 'float', True, True, 0 ],
    'cpu_field2': [ 'cpu', 'nice', 'ticks', None, 'float', True, True, 0 ],
    'cpu_field3': [ 'cpu', 'system', 'ticks', None, 'float', True, True, 0 ],
    'cpu_field4': [ 'cpu', 'idle', 'ticks', None, 'float', True, True, 0 ],
    'cpu_field5': [ 'cpu', 'iowait', 'ticks', None, 'float', True, True, 0 ],
    'cpu_field6': [ 'cpu', 'irq', 'ticks', None, 'float', True, True, 1 ],
    'cpu_field7': [ 'cpu', 'softirq', 'ticks', None, 'float', True, True, 1 ],
    'cpu_field8': [ 'cpu', 'steal', 'ticks', None, 'float', True, True, 2 ],
    'cpu_field9': [ 'cpu', 'guest', 'ticks', None, 'float', True, True, 2 ],
    'cpu_field10': [ 'cpu', 'guest_nice', 'ticks', None, 'float', True, True, 2 ],
    'ctxt': [ 'sched', 'ctxt_switches', 'count', None, 'int', True, True, 0 ],
    'processes': [ 'proc', 'procs_created', 'count', None, 'int', True, True, 0 ],
    'procs_running': [ 'proc', 'procs_running', 'count', None, 'int', True, True, 0 ],
    'procs_blocked': [ 'proc', 'procs_blocked', 'count', None, 'int', True, True, 0 ],
}

# /proc/meminfo fields
GUSTAT_PREFIX_SYS_MEM = 'sys_mem'
GUSTAT_FIELDS_SYS_MEM = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'memtotal': [ 'mem', 'total', 'bytes', None, 'int', False, False, 0 ],
    'memfree': [ 'mem', 'free', 'bytes', None, 'int', True, True, 0 ],
    'buffers': [ 'mem(io)', 'buffers', 'bytes', None, 'int', True, True, 0 ],
    'cached': [ 'mem(io)', 'cache', 'bytes', None, 'int', True, True, 0 ],
    'swapcached': [ 'mem', 'swap_cached', 'bytes', None, 'int', True, True, 1 ],
    'active': [ 'mem', 'active', 'bytes', None, 'int', True, True, 1 ],
    'inactive': [ 'mem', 'inactive', 'bytes', None, 'int', True, True, 1 ],
    'active(anon)': [ 'mem', 'active_anon', 'bytes', None, 'int', True, True, 2 ],
    'inactive(anon)': [ 'mem', 'inactive_anon', 'bytes', None, 'int', True, True, 2 ],
    'active(file)': [ 'mem', 'active_file', 'bytes', None, 'int', True, True, 2 ],
    'inactive(file)': [ 'mem', 'inactive_file', 'bytes', None, 'int', True, True, 2 ],
    'unevictable': [ 'mem', 'unevictable', 'bytes', None, 'int', True, True, 1 ],
    'mlocked': [ 'mem', 'locked', 'bytes', None, 'int', True, True, 1 ],
    'swaptotal': [ 'mem', 'swap_total', 'bytes', None, 'int', False, False, 0 ],
    'swapfree': [ 'mem', 'swap_free', 'bytes', None, 'int', True, True, 0 ],
    'dirty': [ 'mem(io)', 'dirty', 'bytes', None, 'int', True, True, 1 ],
    'writeback': [ 'mem(io)', 'writeback', 'bytes', None, 'int', True, True, 1 ],
    'anonpages': [ 'mem', 'pages_anon', 'bytes', None, 'int', True, True, 1 ],
    'mapped': [ 'mem', 'mapped', 'bytes', None, 'int', True, True, 0 ],
    'shmem': [ 'mem', 'shared', 'bytes', None, 'int', True, True, 0 ],
    'slab': [ 'mem', 'slab', 'bytes', None, 'int', True, True, 1 ],
    'sreclaimable': [ 'mem', 'slab_reclaimable', 'bytes', None, 'int', True, True, 1 ],
    'sunreclaim': [ 'mem', 'slab_unreclaim', 'bytes', None, 'int', True, True, 1 ],
    'kernelstack': [ 'mem', 'kernel_stack', 'bytes', None, 'int', True, True, 1 ],
    'pagetables': [ 'mem', 'page_tables', 'bytes', None, 'int', True, True, 1 ],
    'nfs_unstable': [ 'mem(io)', 'nfs_unstable', 'bytes', None, 'int', True, True, 1 ],
    'bounce': [ 'mem', 'bounce', 'bytes', None, 'int', True, True, 1 ],
    'writebacktmp': [ 'mem(io)', 'writeback_temp', 'bytes', None, 'int', True, True, 1 ],
    'commitlimit': [ 'mem', 'commit_limit', 'bytes', None, 'int', False, False, 1 ],
    'committed_as': [ 'mem', 'committed_as', 'bytes', None, 'int', True, True, 1 ],
    'vmalloctotal': [ 'mem', 'vmalloc_total', 'bytes', None, 'int', False, False, 1 ],
    'vmallocused': [ 'mem', 'vmalloc_used', 'bytes', None, 'int', True, True, 1 ],
    'vmallocchunk': [ 'mem', 'vmalloc_chunk', 'bytes', None, 'int', False, False, 1 ],
    'hardwarecorrupted': [ 'mem', 'hardware_corrupted', 'bytes', None, 'int', True, True, 2 ],
    'anonhugepages': [ 'mem', 'hugepages_anon', 'bytes', None, 'int', True, True, 1 ],
    'hugepages_total': [ 'mem', 'hugepages_total', 'pages', None, 'int', False, False, 1 ],
    'hugepages_free': [ 'mem', 'hugepages_free', 'pages', None, 'int', True, True, 1 ],
    'hugepages_rsvd': [ 'mem', 'hugepages_reserved', 'pages', None, 'int', True, True, 1 ],
    'hugepages_surp': [ 'mem', 'hugepages_surplus', 'pages', None, 'int', True, True, 1 ],
    'hugepagesize': [ 'mem', 'hugepages_size', 'bytes', None, 'int', False, False, 1 ],
    'directmap4k': [ 'mem', 'directmap_4k', 'bytes', None, 'int', True, True, 1 ],
    'directmap2m': [ 'mem', 'directmap_2m', 'bytes', None, 'int', True, True, 1 ],
}

# /proc/vmstat fields
GUSTAT_PREFIX_SYS_VM = 'sys_vm'
GUSTAT_FIELDS_SYS_VM = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'nr_free_pages': [ 'mem', 'free', 'pages', None, 'int', True, True, 0 ],
    'nr_alloc_batch': [ 'mem', 'alloc_batch', 'pages', None, 'int', True, True, 0 ],
    'nr_inactive_anon': [ 'mem', 'inactive_anon', 'pages', None, 'int', True, True, 0 ],
    'nr_active_anon': [ 'mem', 'active_anon', 'pages', None, 'int', True, True, 0 ],
    'nr_inactive_file': [ 'mem', 'inactive_file', 'pages', None, 'int', True, True, 0 ],
    'nr_active_file': [ 'mem', 'active_file', 'pages', None, 'int', True, True, 0 ],
    'nr_unevictable': [ 'mem', 'unevictable', 'pages', None, 'int', True, True, 0 ],
    'nr_mlock': [ 'mem', 'locked', 'pages', None, 'int', True, True, 0 ],
    'nr_anon_pages': [ 'mem', 'pages_anon', 'pages', None, 'int', True, True, 0 ],
    'nr_mapped': [ 'mem', 'mapped', 'pages', None, 'int', True, True, 0 ],
    'nr_file_pages': [ 'mem', 'pages_file', 'pages', None, 'int', True, True, 0 ],
    'nr_dirty': [ 'mem(io)', 'dirty', 'pages', None, 'int', True, True, 0 ],
    'nr_writeback': [ 'mem(io)', 'writeback', 'pages', None, 'int', True, True, 0 ],
    'nr_slab_reclaimable': [ 'mem', 'slab_reclaimable', 'pages', None, 'int', True, True, 0 ],
    'nr_slab_unreclaimable': [ 'mem', 'slab_unreclaimable', 'pages', None, 'int', True, True, 0 ],
    'nr_page_table_pages': [ 'mem', 'page_tables', 'pages', None, 'int', True, True, 0 ],
    'nr_kernel_stack': [ 'mem', 'kernel_stack', 'pages', None, 'int', True, True, 0 ],
    'nr_unstable': [ 'mem(io)', 'nfs_unstable', 'pages', None, 'int', True, True, 0 ],
    'nr_bounce': [ 'mem', 'bounce', 'pages', None, 'int', True, True, 0 ],
    'nr_vmscan_write': [ 'mem', 'vmscan_write', 'pages', None, 'int', True, True, 1 ],
    'nr_vmscan_immediate_reclaim': [ 'mem', 'vmscan_immediate_reclaim', 'pages', None, 'int', True, True, 1 ],
    'nr_writeback_temp': [ 'mem(io)', 'writeback_temp', 'pages', None, 'int', True, True, 1 ],
    'nr_isolated_anon': [ 'mem', 'isolated_anon', 'pages', None, 'int', True, True, 1 ],
    'nr_isolated_file': [ 'mem', 'isolated_file', 'pages', None, 'int', True, True, 1 ],
    'nr_shmem': [ 'mem', 'shared', 'pages', None, 'int', True, True, 0 ],
    'nr_dirtied': [ 'mem(io)', 'dirtied', 'pages', None, 'int', True, True, 0 ],
    'nr_written': [ 'mem(io)', 'written', 'pages', None, 'int', True, True, 0 ],
    'numa_hit': [ 'mem', 'numa_hit', 'pages', None, 'int', True, True, 2 ],
    'numa_miss': [ 'mem', 'numa_miss', 'pages', None, 'int', True, True, 2 ],
    'numa_foreign': [ 'mem', 'numa_foreign', 'pages', None, 'int', True, True, 2 ],
    'numa_interleave': [ 'mem', 'numa_interleave', 'pages', None, 'int', True, True, 2 ],
    'numa_local': [ 'mem', 'numa_local', 'pages', None, 'int', True, True, 2 ],
    'numa_other': [ 'mem', 'numa_other', 'pages', None, 'int', True, True, 2 ],
    'nr_anon_transparent_hugepages': [ 'mem', 'hugepages_anon', 'pages', None, 'int', True, True, 1 ],
    'nr_free_cma': [ 'mem', 'free_cma', 'pages', None, 'int', True, True, 3 ],
    'nr_dirty_threshold': [ 'mem(io)', 'dirty_threshold', 'pages', None, 'int', False, False, 0 ],
    'nr_dirty_background_threshold': [ 'mem(io)', 'dirty_background_threshold', 'pages', None, 'int', False, False, 0 ],
    'pgpgin': [ 'mem', 'pgpgin', 'pages', None, 'int', True, True, 0 ],
    'pgpgout': [ 'mem', 'pgpgout', 'pages', None, 'int', True, True, 0 ],
    'pswpin': [ 'mem', 'pswpin', 'pages', None, 'int', True, True, 0 ],
    'pswpout': [ 'mem', 'pswpout', 'pages', None, 'int', True, True, 0 ],
    'pgalloc_dma': [ 'mem', 'pgalloc_dma', 'pages', None, 'int', True, True, 2 ],
    'pgalloc_dma32': [ 'mem', 'pgalloc_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgalloc_normal': [ 'mem', 'pgalloc_normal', 'pages', None, 'int', True, True, 2 ],
    'pgalloc_movable': [ 'mem', 'pgalloc_movable', 'pages', None, 'int', True, True, 2 ],
    'pgfree': [ 'mem', 'pgfree', 'pages', None, 'int', True, True, 0 ],
    'pgactivate': [ 'mem', 'pgactivate', 'pages', None, 'int', True, True, 0 ],
    'pgdeactivate': [ 'mem', 'pgdeactivate', 'pages', None, 'int', True, True, 0 ],
    'pgfault': [ 'mem', 'pgfault', 'pages', None, 'int', True, True, 0 ],
    'pgmajfault': [ 'mem', 'pgmajfault', 'pages', None, 'int', True, True, 0 ],
    'pgrefill_dma': [ 'mem', 'pgrefill_dma', 'pages', None, 'int', True, True, 2 ],
    'pgrefill_dma32': [ 'mem', 'pgrefill_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgrefill_normal': [ 'mem', 'pgrefill_normal', 'pages', None, 'int', True, True, 2 ],
    'pgrefill_movable': [ 'mem', 'pgrefill_movable', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_kswapd_dma': [ 'mem', 'pgsteal_kswapd_dma', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_kswapd_dma32': [ 'mem', 'pgsteal_kswapd_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_kswapd_normal': [ 'mem', 'pgsteal_kswapd_normal', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_kswapd_movable': [ 'mem', 'pgsteal_kswapd_movable', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_direct_dma': [ 'mem', 'pgsteal_direct_dma', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_direct_dma32': [ 'mem', 'pgsteal_direct_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_direct_normal': [ 'mem', 'pgsteal_direct_normal', 'pages', None, 'int', True, True, 2 ],
    'pgsteal_direct_movable': [ 'mem', 'pgsteal_direct_movable', 'pages', None, 'int', True, True, 2 ],
    'pgscan_kswapd_dma': [ 'mem', 'pgscan_kswapd_dma', 'pages', None, 'int', True, True, 2 ],
    'pgscan_kswapd_dma32': [ 'mem', 'pgscan_kswapd_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgscan_kswapd_normal': [ 'mem', 'pgscan_kswapd_normal', 'pages', None, 'int', True, True, 2 ],
    'pgscan_kswapd_movable': [ 'mem', 'pgscan_kswapd_movable', 'pages', None, 'int', True, True, 2 ],
    'pgscan_direct_dma': [ 'mem', 'pgscan_direct_dma', 'pages', None, 'int', True, True, 2 ],
    'pgscan_direct_dma32': [ 'mem', 'pgscan_direct_dma32', 'pages', None, 'int', True, True, 2 ],
    'pgscan_direct_normal': [ 'mem', 'pgscan_direct_normal', 'pages', None, 'int', True, True, 2 ],
    'pgscan_direct_movable': [ 'mem', 'pgscan_direct_movable', 'pages', None, 'int', True, True, 2 ],
    'pgscan_direct_throttle': [ 'mem', 'pgscan_direct_throttle', 'pages', None, 'int', True, True, 2 ],
    'zone_reclaim_failed': [ 'mem', 'zone_reclaim_failed', 'pages', None, 'int', True, True, 2 ],
    'pginodesteal': [ 'mem', 'pginodesteal', 'pages', None, 'int', True, True, 2 ],
    'slabs_scanned': [ 'mem', 'slabs_scanned', 'pages', None, 'int', True, True, 2 ],
    'kswapd_inodesteal': [ 'mem', 'kswapd_inodesteal', 'pages', None, 'int', True, True, 2 ],
    'kswapd_low_wmark_hit_quickly': [ 'mem', 'kswapd_low_wmark_hit_quickly', 'pages', None, 'int', True, True, 2 ],
    'kswapd_high_wmark_hit_quickly': [ 'mem', 'kswapd_high_wmark_hit_quickly', 'pages', None, 'int', True, True, 2 ],
    'pageoutrun': [ 'mem', 'pageoutrun', 'pages', None, 'int', True, True, 2 ],
    'allocstall': [ 'mem', 'allocstall', 'pages', None, 'int', True, True, 2 ],
    'pgrotated': [ 'mem', 'pgrotated', 'pages', None, 'int', True, True, 2 ],
    'numa_pte_updates': [ 'mem', 'numa_pte_updates', 'pages', None, 'int', True, True, 2 ],
    'numa_huge_pte_updates': [ 'mem', 'numa_huge_pte_updates', 'pages', None, 'int', True, True, 2 ],
    'numa_hint_faults': [ 'mem', 'numa_hint_faults', 'pages', None, 'int', True, True, 2 ],
    'numa_hint_faults_local': [ 'mem', 'numa_hint_faults_local', 'pages', None, 'int', True, True, 2 ],
    'numa_pages_migrated': [ 'mem', 'numa_pages_migrated', 'pages', None, 'int', True, True, 2 ],
    'pgmigrate_success': [ 'mem', 'pgmigrate_success', 'pages', None, 'int', True, True, 2 ],
    'pgmigrate_fail': [ 'mem', 'pgmigrate_fail', 'pages', None, 'int', True, True, 2 ],
    'compact_migrate_scanned': [ 'mem', 'compact_migrate_scanned', 'pages', None, 'int', True, True, 2 ],
    'compact_free_scanned': [ 'mem', 'compact_free_scanned', 'pages', None, 'int', True, True, 2 ],
    'compact_isolated': [ 'mem', 'compact_isolated', 'pages', None, 'int', True, True, 2 ],
    'compact_stall': [ 'mem', 'compact_stall', 'pages', None, 'int', True, True, 2 ],
    'compact_fail': [ 'mem', 'compact_fail', 'pages', None, 'int', True, True, 2 ],
    'compact_success': [ 'mem', 'compact_success', 'pages', None, 'int', True, True, 2 ],
    'htlb_buddy_alloc_success': [ 'mem', 'htlb_buddy_alloc_success', 'pages', None, 'int', True, True, 2 ],
    'htlb_buddy_alloc_fail': [ 'mem', 'htlb_buddy_alloc_fail', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_culled': [ 'mem', 'unevictable_pgs_culled', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_scanned': [ 'mem', 'unevictable_pgs_scanned', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_rescued': [ 'mem', 'unevictable_pgs_rescued', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_mlocked': [ 'mem', 'unevictable_pgs_mlocked', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_munlocked': [ 'mem', 'unevictable_pgs_munlocked', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_cleared': [ 'mem', 'unevictable_pgs_cleared', 'pages', None, 'int', True, True, 2 ],
    'unevictable_pgs_stranded': [ 'mem', 'unevictable_pgs_stranded', 'pages', None, 'int', True, True, 2 ],
    'thp_fault_alloc': [ 'mem', 'hugepages_fault_alloc', 'pages', None, 'int', True, True, 1 ],
    'thp_fault_fallback': [ 'mem', 'hugepages_fault_fallback', 'pages', None, 'int', True, True, 1 ],
    'thp_collapse_alloc': [ 'mem', 'hugepages_collapse_alloc', 'pages', None, 'int', True, True, 1 ],
    'thp_collapse_alloc_failed': [ 'mem', 'hugepages_collapse_alloc_failed', 'pages', None, 'int', True, True, 1 ],
    'thp_split': [ 'mem', 'hugepages_split', 'pages', None, 'int', True, True, 1 ],
    'thp_zero_page_alloc': [ 'mem', 'hugepages_zero_page_alloc', 'pages', None, 'int', True, True, 1 ],
    'thp_zero_page_alloc_failed': [ 'mem', 'hugepages_zero_page_alloc_failed', 'pages', None, 'int', True, True, 1 ],
    'nr_tlb_remote_flush': [ 'mem', 'tlb_remote_flush', 'pages', None, 'int', True, True, 2 ],
    'nr_tlb_remote_flush_received': [ 'mem', 'tlb_remote_flush_received', 'pages', None, 'int', True, True, 2 ],
    'nr_tlb_local_flush_all': [ 'mem', 'tlb_local_flush_all', 'pages', None, 'int', True, True, 2 ],
    'nr_tlb_local_flush_one': [ 'mem', 'tlb_local_flush_one', 'pages', None, 'int', True, True, 2 ],
}

# /proc/diskstats fields
GUSTAT_PREFIX_SYS_DSKS = 'sys_dsks'
GUSTAT_FIELDS_SYS_DSKS = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'field3': [ 'io', 'reads_completed', 'count', None, 'int', True, True, 0 ],
    'field4': [ 'io', 'reads_merged', 'count', None, 'int', True, True, 0 ],
    'field5': [ 'io', 'reads_sectors', 'count', None, 'int', True, True, 0 ],
    'field6': [ 'io', 'reads_elapsed', 'seconds', 0.001, 'float', True, False, 0 ],
    'field7': [ 'io', 'writes_completed', 'count', None, 'int', True, True, 0 ],
    'field8': [ 'io', 'writes_merged', 'count', None, 'int', True, True, 0 ],
    'field9': [ 'io', 'writes_sectors', 'count', None, 'int', True, True, 0 ],
    'field10': [ 'io', 'writes_elapsed', 'seconds', 0.001, 'float', True, False, 0 ],
    'field11': [ 'io', 'ops_ongoing', 'count', None, 'int', False, False, 0 ],
    'field12': [ 'io', 'ops_elapsed', 'seconds', 0.001, 'float', True, False, 0 ],
    'field13': [ 'io', 'ops_elapsed_weighted', 'seconds', 0.001, 'float', True, False, 1 ],
}

# /proc/mountstats fields
GUSTAT_PREFIX_SYS_MNTS = 'sys_mnts'
GUSTAT_FIELDS_SYS_MNTS = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'nfs_events_field1': [ 'io(nfs_events)', 'inode_revalidate', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field2': [ 'io(nfs_events)', 'dnode_revalidate', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field3': [ 'io(nfs_events)', 'data_invalidate', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field4': [ 'io(nfs_events)', 'attr_invalidate', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field5': [ 'io(nfs_events)', 'vfs_open', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field6': [ 'io(nfs_events)', 'vfs_lookup', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field7': [ 'io(nfs_events)', 'vfs_access', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field8': [ 'io(nfs_events)', 'vfs_update_page', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field9': [ 'io(nfs_events)', 'vfs_read_page', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field10': [ 'io(nfs_events)', 'vfs_read_pages_group', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field11': [ 'io(nfs_events)', 'vfs_write_page', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field12': [ 'io(nfs_events)', 'vfs_write_pages_group', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field13': [ 'io(nfs_events)', 'vfs_getdents', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field14': [ 'io(nfs_events)', 'vfs_setattr', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field15': [ 'io(nfs_events)', 'vfs_flush', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field16': [ 'io(nfs_events)', 'vfs_fsync', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field17': [ 'io(nfs_events)', 'vfs_lock', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field18': [ 'io(nfs_events)', 'vfs_release', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field19': [ 'io(nfs_events)', 'congestion_wait', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field20': [ 'io(nfs_events)', 'setattr_trunc', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field21': [ 'io(nfs_events)', 'write_extend', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field22': [ 'io(nfs_events)', 'silly_rename', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field23': [ 'io(nfs_events)', 'reads_short', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field24': [ 'io(nfs_events)', 'writes_short', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field25': [ 'io(nfs_events)', 'delay', 'count', None, 'int', True, True, 2 ],
    'nfs_events_field26': [ 'io(nfs_events)', 'reads_pnfs', 'count', None, 'int', True, True, 1 ],
    'nfs_events_field27': [ 'io(nfs_events)', 'writes_pnfs', 'count', None, 'int', True, True, 1 ],
    'nfs_bytes_field1': [ 'io(nfs_bytes)', 'reads_normal', 'bytes', None, 'int', True, True, 1 ],
    'nfs_bytes_field2': [ 'io(nfs_bytes)', 'writes_normal', 'bytes', None, 'int', True, True, 1 ],
    'nfs_bytes_field3': [ 'io(nfs_bytes)', 'reads_direct', 'bytes', None, 'int', True, True, 1 ],
    'nfs_bytes_field4': [ 'io(nfs_bytes)', 'writes_direct', 'bytes', None, 'int', True, True, 1 ],
    'nfs_bytes_field5': [ 'io(nfs_bytes)', 'reads_nfs', 'bytes', None, 'int', True, True, 0 ],
    'nfs_bytes_field6': [ 'io(nfs_bytes)', 'writes_nfs', 'bytes', None, 'int', True, True, 0 ],
    'nfs_bytes_field7': [ 'io(nfs_bytes)', 'reads_mmap', 'pages', None, 'int', True, True, 1 ],
    'nfs_bytes_field8': [ 'io(nfs_bytes)', 'writes_mmap', 'pages', None, 'int', True, True, 1 ],
    'nfs_ops_field1': [ 'io(nfs_ops)', 'requested', 'count', None, 'int', True, True, 1 ],
    'nfs_ops_field2': [ 'io(nfs_ops)', 'transmitted', 'count', None, 'int', True, True, 1 ],
    'nfs_ops_field3': [ 'io(nfs_ops)', 'timedout', 'count', None, 'int', True, True, 2 ],
    'nfs_ops_field4': [ 'io(nfs_ops)', 'data_sent', 'bytes', None, 'int', True, True, 1 ],
    'nfs_ops_field5': [ 'io(nfs_ops)', 'data_received', 'bytes', None, 'int', True, True, 1 ],
    'nfs_ops_field6': [ 'io(nfs_ops)', 'elapsed_queue_wait', 'seconds', 0.001, 'float', True, False, 2 ],
    'nfs_ops_field7': [ 'io(nfs_ops)', 'elapsed_response_wait', 'seconds', 0.001, 'float', True, False, 2 ],
    'nfs_ops_field8': [ 'io(nfs_ops)', 'elapsed_total', 'seconds', 0.001, 'float', True, False, 1 ],
}
GUSTAT_FIELDS_SYS_MNTS_NFS_OPS = {
    'null',
    'getattr',
    'setattr',
    'lookup',
    'access',
    'readlink',
    'read',
    'write',
    'create',
    'mkdir',
    'symlink',
    'mknod',
    'remove',
    'rmdir',
    'rename',
    'link',
    'readdir',
    'readdirplus',
    'fsstat',
    'fsinfo',
    'pathconf',
    'commit',
}

# /proc/netdev fields
GUSTAT_PREFIX_SYS_NET = 'sys_net'
GUSTAT_FIELDS_SYS_NET = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'field1': [ 'net', 'rx_bytes', 'bytes', None, 'int', True, True, 0 ],
    'field2': [ 'net', 'rx_packets', 'packets', None, 'int', True, True, 0 ],
    'field3': [ 'net', 'rx_errors_device', 'count', None, 'int', True, True, 2 ],
    'field4': [ 'net', 'rx_dropped', 'packets', None, 'int', True, True, 0 ],
    'field5': [ 'net', 'rx_errors_fifo', 'count', None, 'int', True, True, 2 ],
    'field6': [ 'net', 'rx_errors_framing', 'count', None, 'int', True, True, 2 ],
    'field7': [ 'net', 'rx_compressed', 'packets', None, 'int', True, True, 1 ],
    'field8': [ 'net', 'rx_multicasts', 'frames', None, 'int', True, True, 0 ],
    'field9': [ 'net', 'tx_bytes', 'bytes', None, 'int', True, True, 0 ],
    'field10': [ 'net', 'tx_packets', 'packets', None, 'int', True, True, 0 ],
    'field11': [ 'net', 'tx_errors_device', 'count', None, 'int', True, True, 2 ],
    'field12': [ 'net', 'tx_dropped', 'packets', None, 'int', True, True, 0 ],
    'field13': [ 'net', 'tx_errors_fifo', 'count', None, 'int', True, True, 2 ],
    'field14': [ 'net', 'tx_errors_collisions', 'count', None, 'int', True, True, 2 ],
    'field15': [ 'net', 'tx_errors_carrier', 'count', None, 'int', True, True, 2 ],
    'field16': [ 'net', 'tx_compressed', 'packets', None, 'int', True, True, 1 ],
}

# /proc/<pid>/status fields
GUSTAT_PREFIX_PROC_STATUS = 'proc_status'
GUSTAT_FIELDS_PROC_STATUS = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'vmpeak': [ 'mem', 'vsize_peak', 'bytes', None, 'int', True, True, 0 ],
    'vmsize': [ 'mem', 'vsize', 'bytes', None, 'int', True, True, 0 ],
    'vmlck': [ 'mem', 'locked', 'bytes', None, 'int', True, True, 1 ],
    'vmpin': [ 'mem', 'pinned', 'bytes', None, 'int', True, True, 1 ],
    'vmhwm': [ 'mem', 'rss_peak', 'bytes', None, 'int', True, True, 0 ],
    'vmrss': [ 'mem', 'rss', 'bytes', None, 'int', True, True, 0 ],
    'vmdata': [ 'mem', 'data', 'bytes', None, 'int', True, True, 1 ],
    'vmstk': [ 'mem', 'stack', 'bytes', None, 'int', True, True, 1 ],
    'vmexe': [ 'mem', 'executable', 'bytes', None, 'int', True, True, 1 ],
    'vmlib': [ 'mem', 'libraries', 'bytes', None, 'int', True, True, 1 ],
    'vmpte': [ 'mem', 'page_tables', 'bytes', None, 'int', True, True, 1 ],
    'vmswap': [ 'mem', 'swapped', 'bytes', None, 'int', True, True, 0 ],
    'threads': [ 'proc', 'threads', 'count', None, 'int', True, True, 0 ],
    'voluntary_ctxt_switches': [ 'sched', 'ctxt_vol_switches', 'count', None, 'int', True, True, 0 ],
    'nonvoluntary_ctxt_switches': [ 'sched', 'ctxt_nonvol_switches', 'count', None, 'int', True, True, 0 ],
}

# /proc/<pid>/stat fields
GUSTAT_PREFIX_PROC_STAT = 'proc_stat'
GUSTAT_FIELDS_PROC_STAT = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'field9': [ 'mem', 'minflt', 'count', None, 'int', True, True, 0 ],
    'field10': [ 'mem', 'minflt_children', 'count', None, 'int', True, True, 1 ],
    'field11': [ 'mem', 'majflt', 'count', None, 'int', True, True, 0 ],
    'field12': [ 'mem', 'majflt_children', 'count', None, 'int', True, True, 1 ],
    'field13': [ 'cpu', 'utime', 'ticks', None, 'int', True, True, 0 ],
    'field14': [ 'cpu', 'stime', 'ticks', None, 'int', True, True, 0 ],
    'field15': [ 'cpu', 'utime_children', 'ticks', None, 'int', True, True, 1 ],
    'field16': [ 'cpu', 'stime_children', 'ticks', None, 'int', True, True, 1 ],
    'field19': [ 'proc', 'threads', 'count', None, 'int', True, True, 0 ],
    'field22': [ 'mem', 'vsize', 'bytes', None, 'int', True, True, 0 ],
    'field23': [ 'mem', 'rss', 'bytes', None, 'int', True, True, 0 ],
    'field42': [ 'cpu', 'gtime', 'ticks', None, 'int', True, True, 2 ],
    'field43': [ 'cpu', 'gtime_children', 'ticks', None, 'int', True, True, 2 ],
}

# /proc/<pid>/io fields
GUSTAT_PREFIX_PROC_IO = 'proc_io'
GUSTAT_FIELDS_PROC_IO = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'rchar': [ 'io', 'reads_chars', 'chars', None, 'int', True, True, 0 ],
    'wchar': [ 'io', 'writes_chars', 'chars', None, 'int', True, True, 0 ],
    'syscr': [ 'io', 'reads_syscalls', 'count', None, 'int', True, True, 0 ],
    'syscw': [ 'io', 'writes_syscalls', 'count', None, 'int', True, True, 0 ],
    'read_bytes': [ 'io', 'reads_bytes', 'bytes', None, 'int', True, True, 0 ],
    'write_bytes': [ 'io', 'writes_bytes', 'bytes', None, 'int', True, True, 0 ],
    'cancelled_write_bytes': [ 'io', 'writes_bytes_cancelled', 'bytes', None, 'int', True, True, 1 ],
}

# Qemu 'info blockstats' fields
GUSTAT_PREFIX_VIRT_BLKS = 'virt_blks'
GUSTAT_FIELDS_VIRT_BLKS = {
    # key: [ category, metric, unit, coefficient, type, interval-able, rate-able, level ]
    'rd_bytes': [ 'io', 'reads_bytes', 'bytes', None, 'int', True, True, 0 ],
    'wr_bytes': [ 'io', 'writes_bytes', 'bytes', None, 'int', True, True, 0 ],
    'rd_operations': [ 'io', 'reads_ops', 'count', None, 'int', True, True, 0 ],
    'wr_operations': [ 'io', 'writes_ops', 'count', None, 'int', True, True, 0 ],
    'flush_operations': [ 'io', 'flushes_ops', 'count', None, 'int', True, True, 1 ],
    'rd_total_time_ns': [ 'io', 'reads_elapsed', 'seconds', 0.000000001, 'float', True, False, 0 ],
    'wr_total_time_ns': [ 'io', 'writes_elapsed', 'seconds', 0.000000001, 'float', True, False, 0 ],
    'flush_total_time_ns': [ 'io', 'flushes_elapsed', 'seconds', 0.000000001, 'float', True, False, 1 ],
}


#------------------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------------------

class GUStatData:
    """
    Global Statistics data container/parser
    """

    #------------------------------------------------------------------------------
    # CONSTRUCTORS / DESTRUCTOR
    #------------------------------------------------------------------------------

    def __init__(self, _bInterval, _bRate):
        # Fields
        self.__bInterval = bool(_bInterval)
        self.__bRate = bool(_bRate)
        self.__reMultiSpaces = re.compile('\s\s+')
        self.__iCpuCount = None
        self.dStats = dict()


    #------------------------------------------------------------------------------
    # METHODS
    #------------------------------------------------------------------------------

    #
    # Data
    #

    def __makeField(self, _dStatFields, _sKey, _sValue, _fCoefficient = None, _sMetricPrefix = None):
        """
        Build a global statistics field (dictonary), mapping:
         'category': field category
         'metric': field metric
         'unit': field unit
         'value': field value
         'interval': interval-able flag
         'rate': rate-able flag
        """

        if _sKey not in _dStatFields:
            return None
        try:
            mValue = float(_sValue)
        except:
            mValue = 0.0
        fCoefficient = _dStatFields[_sKey][3]
        if _fCoefficient is not None:
            mValue *= _fCoefficient
        elif fCoefficient is not None:
            mValue *= fCoefficient
        sType = _dStatFields[_sKey][4]
        if sType == 'int':
            mValue = int(mValue)
        #elif sType == 'float': already a float
        sMetric = _dStatFields[_sKey][1];
        if _sMetricPrefix is not None:
            sMetric = _sMetricPrefix+'_'+sMetric
        return {
            'category': _dStatFields[_sKey][0],
            'metric': sMetric,
            'unit': _dStatFields[_sKey][2],
            'value': mValue,
            'interval': _dStatFields[_sKey][5],
            'rate': _dStatFields[_sKey][6],
            'level': _dStatFields[_sKey][7],
       }


    def __storeField(self, _sKeyPrefix, _sKeyObject, _dField, _iLevel):
        if _dField is None:
            return
        if self.__bInterval:
            if not _dField['interval']:
                return
            if self.__bRate and not _dField['rate']:
                return
        if _dField['level'] > _iLevel:
            return
        if _sKeyObject is None:
            _sKeyObject = '-'
        self.dStats[_sKeyPrefix+','+_sKeyObject+','+_dField['category']+':'+_dField['metric']] = _dField

    #
    # Parsers
    #

    def parseStat_sys_cpu(self, _iLevel):
        global GUSTAT_PREFIX_SYS_CPU
        global GUSTAT_FIELDS_SYS_CPU

        sFile = '/proc/cpuinfo'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        iQuantity = int(0)
        sId = None
        for sLine in oFile:
            lWords = [_s.strip() for _s in sLine.lower().split(':')]
            if len(lWords) < 2:
                continue
            if lWords[0] == 'processor':
                iQuantity += 1
                sId = 'cpu'+lWords[1]
            else:
                if sId is None:
                    continue
                if lWords[0] == 'model name':
                    try:
                        lWords[1] = lWords[1].rsplit('@', 1)[1].strip().lower()
                        if lWords[1][-3:] == 'ghz':
                            lWords[1] = int(1000000000.0*float(lWords[1][:-3]))
                        elif lWords[1][-3:] == 'mhz':
                            lWords[1] = int(1000000.0*float(lWords[1][:-3]))
                        elif lWords[1][-3:] == 'khz':
                            lWords[1] = int(1000.0*float(lWords[1][:-3]))
                        elif lWords[1][-2:] == 'hz':
                            lWords[1] = int(lWords[1][:-2])
                    except:
                        continue
                dField = self.__makeField(GUSTAT_FIELDS_SYS_CPU, lWords[0], lWords[1])
                self.__storeField(GUSTAT_PREFIX_SYS_CPU, sId, dField, _iLevel)
        self.__iCpuCount = iQuantity
        dField = self.__makeField(GUSTAT_FIELDS_SYS_CPU, 'count', self.__iCpuCount)
        self.__storeField(GUSTAT_PREFIX_SYS_CPU, 'cpu', dField, _iLevel)
        oFile.close()


    def parseStat_sys_load(self, _iLevel):
        global GUSTAT_PREFIX_SYS_LOAD
        global GUSTAT_FIELDS_SYS_LOAD

        sFile = '/proc/loadavg'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        lWords = oFile.readline().split()
        if len(lWords) >= 3:
            for i in range(0, 3):
                if self.__iCpuCount is not None:
                    dField = self.__makeField(GUSTAT_FIELDS_SYS_LOAD, 'field'+str(i), float(lWords[i]) / self.__iCpuCount)
                    self.__storeField(GUSTAT_PREFIX_SYS_LOAD, 'normalized', dField, _iLevel)
                dField = self.__makeField(GUSTAT_FIELDS_SYS_LOAD, 'field'+str(i), lWords[i])
                self.__storeField(GUSTAT_PREFIX_SYS_LOAD, 'total', dField, _iLevel)
        else:
            sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
        oFile.close()


    def parseStat_sys_stat(self, _iLevel, _bCpuDetail):
        global GUSTAT_PREFIX_SYS_STAT
        global GUSTAT_FIELDS_SYS_STAT

        sFile = '/proc/stat'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        for sLine in oFile:
            lWords = self.__reMultiSpaces.sub(' ', sLine.lower()).split()
            if len(lWords) < 2:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            if lWords[0].startswith('cpu'):
                if len(lWords) < 11:
                    sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                    break
                sCpu = lWords[0]
                if sCpu == 'cpu':
                    if _bCpuDetail:
                        continue
                else:
                    if not _bCpuDetail:
                        continue
                for i in range(1, 11):
                    if sCpu == 'cpu' and self.__iCpuCount is not None:
                        dField = self.__makeField(GUSTAT_FIELDS_SYS_STAT, 'cpu_field'+str(i), float(lWords[i]) / self.__iCpuCount)
                        self.__storeField(GUSTAT_PREFIX_SYS_STAT, sCpu+'_n', dField, _iLevel)
                    else:
                        dField = self.__makeField(GUSTAT_FIELDS_SYS_STAT, 'cpu_field'+str(i), lWords[i])
                        self.__storeField(GUSTAT_PREFIX_SYS_STAT, sCpu, dField, _iLevel)
            else:
                dField = self.__makeField(GUSTAT_FIELDS_SYS_STAT, lWords[0], lWords[1])
                self.__storeField(GUSTAT_PREFIX_SYS_STAT, None, dField, _iLevel)
        oFile.close()


    def parseStat_sys_mem(self, _iLevel):
        global GUSTAT_PREFIX_SYS_MEM
        global GUSTAT_FIELDS_SYS_MEM

        sFile = '/proc/meminfo'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        for sLine in oFile:
            lWords = [_s.strip() for _s in sLine.lower().split(':')]
            if len(lWords) < 2:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            if lWords[1].endswith('gb'):
                dField = self.__makeField(GUSTAT_FIELDS_SYS_MEM, lWords[0], lWords[1][0:-2], _fCoefficient=1073741824.0)
            elif lWords[1].endswith(' mb'):
                dField = self.__makeField(GUSTAT_FIELDS_SYS_MEM, lWords[0], lWords[1][0:-2], _fCoefficient=1048576.0)
            elif lWords[1].endswith(' kb'):
                dField = self.__makeField(GUSTAT_FIELDS_SYS_MEM, lWords[0], lWords[1][0:-2], _fCoefficient=1024.0)
            else:
                dField = self.__makeField(GUSTAT_FIELDS_SYS_MEM, lWords[0], lWords[1])
            self.__storeField(GUSTAT_PREFIX_SYS_MEM, None, dField, _iLevel)
        oFile.close()


    def parseStat_sys_vm(self, _iLevel):
        global GUSTAT_PREFIX_SYS_VM
        global GUSTAT_FIELDS_SYS_VM

        sFile = '/proc/vmstat'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        for sLine in oFile:
            lWords = sLine.lower().split(' ')
            if len(lWords) < 2:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            dField = self.__makeField(GUSTAT_FIELDS_SYS_VM, lWords[0], lWords[1])
            self.__storeField(GUSTAT_PREFIX_SYS_VM, None, dField, _iLevel)
        oFile.close()


    def parseStat_sys_dsks(self, _iLevel, _sDevice, _bDevicePrefix):
        global GUSTAT_PREFIX_SYS_DSKS
        global GUSTAT_FIELDS_SYS_DSKS

        sFile = '/proc/diskstats'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        sDevice = None
        for sLine in oFile:
            lWords = self.__reMultiSpaces.sub(' ', sLine.lower().strip()).split()
            if len(lWords) < 14:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            if _sDevice is None \
                or (_bDevicePrefix and lWords[2].startswith(_sDevice)) \
                or lWords[2] == _sDevice:
                sDevice = lWords[2]
            else:
                sDevice = None
            if sDevice is None:
                continue
            for i in range(3, 14):
                dField = self.__makeField(GUSTAT_FIELDS_SYS_DSKS, 'field'+str(i), lWords[i])
                self.__storeField(GUSTAT_PREFIX_SYS_DSKS, sDevice, dField, _iLevel)
        oFile.close()


    def parseStat_sys_mnts(self, _iLevel, _sDevice, _bDevicePrefix):
        global GUSTAT_PREFIX_SYS_MNTS
        global GUSTAT_FIELDS_SYS_MNTS

        sFile = '/proc/self/mountstats'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        sDevice = None
        sType = None
        for sLine in oFile:
            lWords = self.__reMultiSpaces.sub(' ', sLine.lower().strip()).split()
            if len(lWords) < 2:
                continue
            lWords[0] = lWords[0].strip(':')
            if lWords[0] == 'device':
                if len(lWords) < 8:
                    sys.stderr.write('ERROR: Badly/unexpectedly formatted file [nfs:events]; %s\n' % sFile)
                    break
                if _sDevice is None \
                    or (_bDevicePrefix and lWords[4].startswith(_sDevice)) \
                    or lWords[4] == _sDevice:
                    sDevice = lWords[4]
                    sType = lWords[7]
                else:
                    sDevice = None
                    sType = None
                continue
            if sDevice is None or sType is None:
                continue
            if sType == 'nfs':
                if lWords[0] == 'events':
                    if len(lWords) < 28:
                        sys.stderr.write('ERROR: Badly/unexpectedly formatted file [nfs:events]; %s\n' % sFile)
                        break
                    for i in range(1, 28):
                        dField = self.__makeField(GUSTAT_FIELDS_SYS_MNTS, 'nfs_events_field'+str(i), lWords[i])
                        self.__storeField(GUSTAT_PREFIX_SYS_MNTS, sDevice, dField, _iLevel)
                elif lWords[0] == 'bytes':
                    if len(lWords) < 9:
                        sys.stderr.write('ERROR: Badly/unexpectedly formatted file [nfs:bytes]; %s\n' % sFile)
                        break
                    for i in range(1, 9):
                        dField = self.__makeField(GUSTAT_FIELDS_SYS_MNTS, 'nfs_bytes_field'+str(i), lWords[i])
                        self.__storeField(GUSTAT_PREFIX_SYS_MNTS, sDevice, dField, _iLevel)
                elif lWords[0] in GUSTAT_FIELDS_SYS_MNTS_NFS_OPS:
                    if len(lWords) < 9:
                        sys.stderr.write('ERROR: Badly/unexpectedly formatted file [nfs:ops]; %s\n' % sFile)
                        break
                    for i in range(1, 9):
                        dField = self.__makeField(GUSTAT_FIELDS_SYS_MNTS, 'nfs_ops_field'+str(i), lWords[i], _sMetricPrefix=lWords[0])
                        self.__storeField(GUSTAT_PREFIX_SYS_MNTS, sDevice, dField, _iLevel)
        oFile.close()


    def parseStat_sys_net(self, _iLevel, _sDevice, _bDevicePrefix):
        global GUSTAT_PREFIX_SYS_NET
        global GUSTAT_FIELDS_SYS_NET

        sFile = '/proc/net/dev'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        sDevice = None
        iLine = 0
        for sLine in oFile:
            iLine += 1
            if iLine < 3:
                continue
            lWords = self.__reMultiSpaces.sub(' ', sLine.lower().strip()).split()
            if len(lWords) < 17:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            lWords[0] = lWords[0].strip(':')
            if _sDevice is None \
                or (_bDevicePrefix and lWords[0].startswith(_sDevice)) \
                or lWords[0] == _sDevice:
                sDevice = lWords[0]
            else:
                sDevice = None
            if sDevice is None:
                continue
            for i in range(1, 17):
                dField = self.__makeField(GUSTAT_FIELDS_SYS_NET, 'field'+str(i), lWords[i])
                self.__storeField(GUSTAT_PREFIX_SYS_NET, sDevice, dField, _iLevel)
        oFile.close()


    def parseStat_proc_status(self, _iLevel, _iPid):
        global GUSTAT_PREFIX_PROC_STATUS
        global GUSTAT_FIELDS_PROC_STATUS

        sPid = str(_iPid)
        sFile = '/proc/'+sPid+'/status'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable %s\n' % sFile)
            return
        for sLine in oFile:
            lWords = [_s.strip() for _s in sLine.lower().split(':')]
            if len(lWords) < 2:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            if lWords[1].endswith('gb'):
                dField = self.__makeField(GUSTAT_FIELDS_PROC_STATUS, lWords[0], lWords[1][0:-2], _fCoefficient=1073741824.0)
            elif lWords[1].endswith(' mb'):
                dField = self.__makeField(GUSTAT_FIELDS_PROC_STATUS, lWords[0], lWords[1][0:-2], _fCoefficient=1048576.0)
            elif lWords[1].endswith(' kb'):
                dField = self.__makeField(GUSTAT_FIELDS_PROC_STATUS, lWords[0], lWords[1][0:-2], _fCoefficient=1024.0)
            else:
                dField = self.__makeField(GUSTAT_FIELDS_PROC_STATUS, lWords[0], lWords[1])
            self.__storeField(GUSTAT_PREFIX_PROC_STATUS, sPid, dField, _iLevel)
        oFile.close()


    def parseStat_proc_stat(self, _iLevel, _iPid):
        global GUSTAT_PREFIX_PROC_STAT
        global GUSTAT_FIELDS_PROC_STAT

        sPid = str(_iPid)
        sFile = '/proc/'+sPid+'/stat'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        lWords = oFile.readline().split()
        if len(lWords) >= 44:
            for i in [9, 10, 11, 12, 13, 14, 15, 16, 19, 22, 23, 42, 43]:
                dField = self.__makeField(GUSTAT_FIELDS_PROC_STAT, 'field'+str(i), lWords[i])
                self.__storeField(GUSTAT_PREFIX_PROC_STAT, sPid, dField, _iLevel)
        else:
            sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
        oFile.close()


    def parseStat_proc_io(self, _iLevel, _iPid):
        global GUSTAT_PREFIX_PROC_IO
        global GUSTAT_FIELDS_PROC_IO

        sPid = str(_iPid)
        sFile = '/proc/'+sPid+'/io'
        try:
            oFile = open(sFile, 'r')
        except:
            sys.stderr.write('ERROR: Missing/unreadable file; %s\n' % sFile)
            return
        for sLine in oFile:
            lWords = [_s.strip() for _s in sLine.lower().split(':')]
            if len(lWords) < 2:
                continue
            dField = self.__makeField(GUSTAT_FIELDS_PROC_IO, lWords[0], lWords[1])
            self.__storeField(GUSTAT_PREFIX_PROC_IO, sPid, dField, _iLevel)
        oFile.close()


    def parseStat_virt_blks(self, _iLevel, _sGuest, _sDevice, _bDevicePrefix):
        global GUSTAT_PREFIX_VIRT_BLKS
        global GUSTAT_FIELDS_VIRT_BLKS

        lCommandArgs = ['virsh', '--quiet', 'qemu-monitor-command', '--hmp', _sGuest, 'info', 'blockstats']
        try:
            bOutput = SP.check_output(lCommandArgs)
        except:
            sys.stderr.write('ERROR: Command failed; %s\n' % ' '.join(lCommandArgs))
            return
        sDevice = None
        for sLine in bOutput.decode(sys.stdout.encoding).splitlines():
            lWords = sLine.lower().split(' ')
            if len(lWords) < 2:
                continue
            if len(lWords) < 9:
                sys.stderr.write('ERROR: Badly/unexpectedly formatted file; %s\n' % sFile)
                break
            lWords[0] = lWords[0].strip(':')
            if _sDevice is None \
                or (_bDevicePrefix and lWords[0].startswith(_sDevice)) \
                or lWords[0] == _sDevice:
                sDevice = lWords[0]
            else:
                sDevice = None
            if sDevice is None:
                continue
            for i in range(1, 9):
                (sMetric, sValue) = lWords[i].split('=', 1)
                dField = self.__makeField(GUSTAT_FIELDS_VIRT_BLKS, sMetric, sValue)
                self.__storeField(GUSTAT_PREFIX_VIRT_BLKS, _sGuest+':'+sDevice, dField, _iLevel)


    #
    # Output
    #

    def __str__(self):
        sStr = ''
        for sKey in sorted(self.dStats.keys()):
            dField = self.dStats[sKey]
            sStr += sKey+'['+dField['unit']+']='+str(dField['value'])+'\n'
        return sStr


    def display(self, _sTimestamp, _sIntFormat, _sFloatFormat, _bZeroHide, _iJustify):
        for sKey in sorted(self.dStats.keys()):
            dField = self.dStats[sKey]
            mValue = dField['value']
            if _sIntFormat is not None and isinstance(mValue, int):
                sValue = _sIntFormat.format(mValue)
            elif _sFloatFormat is not None and isinstance(mValue, float):
                sValue = _sFloatFormat.format(mValue)
            else:
                sValue = str(mValue)
            if _bZeroHide:
                bNonZero = False
                for c in  sValue:
                    if c not in '0-.,':
                        bNonZero = True
                        break
                if not bNonZero:
                    continue
            sLabel = sKey
            if _iJustify > 0:
                if _sTimestamp is not None:
                    sLabel = _sTimestamp+','+sLabel+'['+dField['unit']+']'
                else:
                    sLabel += '['+dField['unit']+']'
                iValuePosition = _iJustify - len(sValue)
                if len(sLabel) > iValuePosition - 1:
                    sLabel = sLabel[0:iValuePosition-1]+'~'
                else:
                    sLabel = (sLabel+':').ljust(iValuePosition-1, '.')+' '
            else:
                if _sTimestamp is not None:
                    sLabel = _sTimestamp+','+sLabel+','+dField['unit']+','
                else:
                    sLabel = ','+sLabel+','+dField['unit']+','
            sys.stdout.write('%s%s\n' % (sLabel, sValue))
