#!/bin/bash

:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx
CREATE DATABASE "gustat";
__EOF__



# NOTE: For optimal performances, adapt the shard durations such as to have
#       compacted TSM files size around ~100MB
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
CREATE RETENTION POLICY "long" ON "gustat" DURATION 30d REPLICATION 1 SHARD DURATION 3h DEFAULT;
CREATE RETENTION POLICY "short" ON "gustat" DURATION 5d REPLICATION 1 SHARD DURATION 3h;
CREATE RETENTION POLICY "temporary" ON "gustat" DURATION 48h REPLICATION 1 SHARD DURATION 3h;
CREATE RETENTION POLICY "history" ON "gustat" DURATION 3650d REPLICATION 1;
DROP RETENTION POLICY "autogen" ON "gustat";
SHOW RETENTION POLICIES;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.cpu_info" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.cpu_info" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  LAST("cores_count") AS "cores_count"
, NON_NEGATIVE_DERIVATIVE(LAST("idle_seconds"),1s) AS "idle_load"
, NON_NEGATIVE_DERIVATIVE(LAST("iowait_seconds"),1s) AS "iowait_load"
, NON_NEGATIVE_DERIVATIVE(LAST("irq_count"),1s) AS "irq_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("irq_seconds"),1s) AS "irq_load"
, LAST("logical_count") AS "logical_count"
, NON_NEGATIVE_DERIVATIVE(LAST("nice_seconds"),1s) AS "nice_load"
, LAST("physical_count") AS "physical_count"
, NON_NEGATIVE_DERIVATIVE(LAST("softirq_count"),1s) AS "softirq_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("softirq_seconds"),1s) AS "softirq_load"
, NON_NEGATIVE_DERIVATIVE(LAST("system_seconds"),1s) AS "system_load"
, NON_NEGATIVE_DERIVATIVE(LAST("user_seconds"),1s) AS "user_load"
INTO
  "gustat"."temporary"."cpu_info"
FROM
  "gustat"."long"."cpu_info"
GROUP BY
  time(5s),"task","serie","host"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.cpu_info_cores_count" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_cores_count" ON "gustat" BEGIN SELECT MIN("cores_count") AS "MIN_cores_count", MEAN("cores_count") AS "MEAN_cores_count", MEDIAN("cores_count") AS "MEDIAN_cores_count", MAX("cores_count") AS "MAX_cores_count" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_iowait_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_iowait_load" ON "gustat" BEGIN SELECT MIN("iowait_load") AS "MIN_iowait_load", MEAN("iowait_load") AS "MEAN_iowait_load", MEDIAN("iowait_load") AS "MEDIAN_iowait_load", MAX("iowait_load") AS "MAX_iowait_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_irq_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_irq_load" ON "gustat" BEGIN SELECT MIN("irq_load") AS "MIN_irq_load", MEAN("irq_load") AS "MEAN_irq_load", MEDIAN("irq_load") AS "MEDIAN_irq_load", MAX("irq_load") AS "MAX_irq_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_nice_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_nice_load" ON "gustat" BEGIN SELECT MIN("nice_load") AS "MIN_nice_load", MEAN("nice_load") AS "MEAN_nice_load", MEDIAN("nice_load") AS "MEDIAN_nice_load", MAX("nice_load") AS "MAX_nice_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_physical_count" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_physical_count" ON "gustat" BEGIN SELECT MIN("physical_count") AS "MIN_physical_count", MEAN("physical_count") AS "MEAN_physical_count", MEDIAN("physical_count") AS "MEDIAN_physical_count", MAX("physical_count") AS "MAX_physical_count" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_softirq_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_softirq_load" ON "gustat" BEGIN SELECT MIN("softirq_load") AS "MIN_softirq_load", MEAN("softirq_load") AS "MEAN_softirq_load", MEDIAN("softirq_load") AS "MEDIAN_softirq_load", MAX("softirq_load") AS "MAX_softirq_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_system_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_system_load" ON "gustat" BEGIN SELECT MIN("system_load") AS "MIN_system_load", MEAN("system_load") AS "MEAN_system_load", MEDIAN("system_load") AS "MEDIAN_system_load", MAX("system_load") AS "MAX_system_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.cpu_info_user_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.cpu_info_user_load" ON "gustat" BEGIN SELECT MIN("user_load") AS "MIN_user_load", MEAN("user_load") AS "MEAN_user_load", MEDIAN("user_load") AS "MEDIAN_user_load", MAX("user_load") AS "MAX_user_load" INTO "gustat"."history"."cpu_info" FROM "gustat"."temporary"."cpu_info" GROUP BY time(1d),* END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.io_disk" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.io_disk" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("reads_completed_count"),1s) AS "reads_completed_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("reads_elapsed_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("reads_completed_count")) AS "reads_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("reads_sectors_count"),1s) AS "reads_sectors_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("writes_completed_count"),1s) AS "writes_completed_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("writes_elapsed_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("writes_completed_count")) AS "writes_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("writes_sectors_count"),1s) AS "writes_sectors_per_second"
INTO
  "gustat"."temporary"."io_disk"
FROM
  "gustat"."long"."io_disk"
GROUP BY
  time(5s),"task","serie","host","device"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.io_disk" ON "gustat";
DROP CONTINUOUS QUERY "history.io_disk_reads_completed_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_reads_completed_per_second" ON "gustat" BEGIN SELECT MIN("reads_completed_per_second") AS "MIN_reads_completed_per_second", MEAN("reads_completed_per_second") AS "MEAN_reads_completed_per_second", MEDIAN("reads_completed_per_second") AS "MEDIAN_reads_completed_per_second", MAX("reads_completed_per_second") AS "MAX_reads_completed_per_second" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.io_disk_reads_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_reads_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("reads_latency_seconds_per_op") AS "MIN_reads_latency_seconds_per_op", MEAN("reads_latency_seconds_per_op") AS "MEAN_reads_latency_seconds_per_op", MEDIAN("reads_latency_seconds_per_op") AS "MEDIAN_reads_latency_seconds_per_op", MAX("reads_latency_seconds_per_op") AS "MAX_reads_latency_seconds_per_op" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.io_disk_reads_sectors_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_reads_sectors_per_second" ON "gustat" BEGIN SELECT MIN("reads_sectors_per_second") AS "MIN_reads_sectors_per_second", MEAN("reads_sectors_per_second") AS "MEAN_reads_sectors_per_second", MEDIAN("reads_sectors_per_second") AS "MEDIAN_reads_sectors_per_second", MAX("reads_sectors_per_second") AS "MAX_reads_sectors_per_second" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.io_disk_writes_completed_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_writes_completed_per_second" ON "gustat" BEGIN SELECT MIN("writes_completed_per_second") AS "MIN_writes_completed_per_second", MEAN("writes_completed_per_second") AS "MEAN_writes_completed_per_second", MEDIAN("writes_completed_per_second") AS "MEDIAN_writes_completed_per_second", MAX("writes_completed_per_second") AS "MAX_writes_completed_per_second" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.io_disk_writes_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_writes_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("writes_latency_seconds_per_op") AS "MIN_writes_latency_seconds_per_op", MEAN("writes_latency_seconds_per_op") AS "MEAN_writes_latency_seconds_per_op", MEDIAN("writes_latency_seconds_per_op") AS "MEDIAN_writes_latency_seconds_per_op", MAX("writes_latency_seconds_per_op") AS "MAX_writes_latency_seconds_per_op" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.io_disk_writes_sectors_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_disk_writes_sectors_per_second" ON "gustat" BEGIN SELECT MIN("writes_sectors_per_second") AS "MIN_writes_sectors_per_second", MEAN("writes_sectors_per_second") AS "MEAN_writes_sectors_per_second", MEDIAN("writes_sectors_per_second") AS "MEDIAN_writes_sectors_per_second", MAX("writes_sectors_per_second") AS "MAX_writes_sectors_per_second" INTO "gustat"."history"."io_disk" FROM "gustat"."temporary"."io_disk" GROUP BY time(1d),* END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.io_mount_nfs" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.io_mount_nfs" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("io_reads_server_bytes"),1s) AS "io_reads_server_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_writes_server_bytes"),1s) AS "io_writes_server_bytes_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_create_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_create_requested_count")) AS "rpc_create_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_create_requested_count"),1s) AS "rpc_create_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_mkdir_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_mkdir_requested_count")) AS "rpc_mkdir_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_mkdir_requested_count"),1s) AS "rpc_mkdir_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_read_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_read_requested_count")) AS "rpc_read_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_read_requested_count"),1s) AS "rpc_read_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_readdir_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_readdir_requested_count")) AS "rpc_readdir_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_readdir_requested_count"),1s) AS "rpc_readdir_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_readdirplus_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_readdirplus_requested_count")) AS "rpc_readdirplus_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_readdirplus_requested_count"),1s) AS "rpc_readdirplus_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_remove_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_remove_requested_count")) AS "rpc_remove_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_remove_requested_count"),1s) AS "rpc_remove_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_rmdir_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_rmdir_requested_count")) AS "rpc_rmdir_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_rmdir_requested_count"),1s) AS "rpc_rmdir_requested_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("rpc_write_elapsed_total_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("rpc_write_requested_count")) AS "rpc_write_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("rpc_write_requested_count"),1s) AS "rpc_write_requested_per_second"
INTO
  "gustat"."temporary"."io_mount_nfs"
FROM
  "gustat"."long"."io_mount_nfs"
GROUP BY
  time(60s),"host","path"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.io_mount_nfs_io_reads_server_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_io_reads_server_bytes_per_second" ON "gustat" BEGIN SELECT MIN("io_reads_server_bytes_per_second") AS "MIN_io_reads_server_bytes_per_second", MEAN("io_reads_server_bytes_per_second") AS "MEAN_io_reads_server_bytes_per_second", MEDIAN("io_reads_server_bytes_per_second") AS "MEDIAN_io_reads_server_bytes_per_second", MAX("io_reads_server_bytes_per_second") AS "MAX_io_reads_server_bytes_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_io_writes_server_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_io_writes_server_bytes_per_second" ON "gustat" BEGIN SELECT MIN("io_writes_server_bytes_per_second") AS "MIN_io_writes_server_bytes_per_second", MEAN("io_writes_server_bytes_per_second") AS "MEAN_io_writes_server_bytes_per_second", MEDIAN("io_writes_server_bytes_per_second") AS "MEDIAN_io_writes_server_bytes_per_second", MAX("io_writes_server_bytes_per_second") AS "MAX_io_writes_server_bytes_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_create_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_create_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_create_latency_seconds_per_op") AS "MIN_rpc_create_latency_seconds_per_op", MEAN("rpc_create_latency_seconds_per_op") AS "MEAN_rpc_create_latency_seconds_per_op", MEDIAN("rpc_create_latency_seconds_per_op") AS "MEDIAN_rpc_create_latency_seconds_per_op", MAX("rpc_create_latency_seconds_per_op") AS "MAX_rpc_create_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_create_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_create_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_create_requested_per_second") AS "MIN_rpc_create_requested_per_second", MEAN("rpc_create_requested_per_second") AS "MEAN_rpc_create_requested_per_second", MEDIAN("rpc_create_requested_per_second") AS "MEDIAN_rpc_create_requested_per_second", MAX("rpc_create_requested_per_second") AS "MAX_rpc_create_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_mkdir_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_mkdir_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_mkdir_latency_seconds_per_op") AS "MIN_rpc_mkdir_latency_seconds_per_op", MEAN("rpc_mkdir_latency_seconds_per_op") AS "MEAN_rpc_mkdir_latency_seconds_per_op", MEDIAN("rpc_mkdir_latency_seconds_per_op") AS "MEDIAN_rpc_mkdir_latency_seconds_per_op", MAX("rpc_mkdir_latency_seconds_per_op") AS "MAX_rpc_mkdir_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_mkdir_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_mkdir_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_mkdir_requested_per_second") AS "MIN_rpc_mkdir_requested_per_second", MEAN("rpc_mkdir_requested_per_second") AS "MEAN_rpc_mkdir_requested_per_second", MEDIAN("rpc_mkdir_requested_per_second") AS "MEDIAN_rpc_mkdir_requested_per_second", MAX("rpc_mkdir_requested_per_second") AS "MAX_rpc_mkdir_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_read_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_read_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_read_latency_seconds_per_op") AS "MIN_rpc_read_latency_seconds_per_op", MEAN("rpc_read_latency_seconds_per_op") AS "MEAN_rpc_read_latency_seconds_per_op", MEDIAN("rpc_read_latency_seconds_per_op") AS "MEDIAN_rpc_read_latency_seconds_per_op", MAX("rpc_read_latency_seconds_per_op") AS "MAX_rpc_read_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_read_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_read_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_read_requested_per_second") AS "MIN_rpc_read_requested_per_second", MEAN("rpc_read_requested_per_second") AS "MEAN_rpc_read_requested_per_second", MEDIAN("rpc_read_requested_per_second") AS "MEDIAN_rpc_read_requested_per_second", MAX("rpc_read_requested_per_second") AS "MAX_rpc_read_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdir_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdir_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_readdir_latency_seconds_per_op") AS "MIN_rpc_readdir_latency_seconds_per_op", MEAN("rpc_readdir_latency_seconds_per_op") AS "MEAN_rpc_readdir_latency_seconds_per_op", MEDIAN("rpc_readdir_latency_seconds_per_op") AS "MEDIAN_rpc_readdir_latency_seconds_per_op", MAX("rpc_readdir_latency_seconds_per_op") AS "MAX_rpc_readdir_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdir_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdir_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_readdir_requested_per_second") AS "MIN_rpc_readdir_requested_per_second", MEAN("rpc_readdir_requested_per_second") AS "MEAN_rpc_readdir_requested_per_second", MEDIAN("rpc_readdir_requested_per_second") AS "MEDIAN_rpc_readdir_requested_per_second", MAX("rpc_readdir_requested_per_second") AS "MAX_rpc_readdir_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdirplus_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdirplus_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_readdirplus_latency_seconds_per_op") AS "MIN_rpc_readdirplus_latency_seconds_per_op", MEAN("rpc_readdirplus_latency_seconds_per_op") AS "MEAN_rpc_readdirplus_latency_seconds_per_op", MEDIAN("rpc_readdirplus_latency_seconds_per_op") AS "MEDIAN_rpc_readdirplus_latency_seconds_per_op", MAX("rpc_readdirplus_latency_seconds_per_op") AS "MAX_rpc_readdirplus_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdirplus_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_readdirplus_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_readdirplus_requested_per_second") AS "MIN_rpc_readdirplus_requested_per_second", MEAN("rpc_readdirplus_requested_per_second") AS "MEAN_rpc_readdirplus_requested_per_second", MEDIAN("rpc_readdirplus_requested_per_second") AS "MEDIAN_rpc_readdirplus_requested_per_second", MAX("rpc_readdirplus_requested_per_second") AS "MAX_rpc_readdirplus_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_remove_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_remove_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_remove_latency_seconds_per_op") AS "MIN_rpc_remove_latency_seconds_per_op", MEAN("rpc_remove_latency_seconds_per_op") AS "MEAN_rpc_remove_latency_seconds_per_op", MEDIAN("rpc_remove_latency_seconds_per_op") AS "MEDIAN_rpc_remove_latency_seconds_per_op", MAX("rpc_remove_latency_seconds_per_op") AS "MAX_rpc_remove_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_remove_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_remove_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_remove_requested_per_second") AS "MIN_rpc_remove_requested_per_second", MEAN("rpc_remove_requested_per_second") AS "MEAN_rpc_remove_requested_per_second", MEDIAN("rpc_remove_requested_per_second") AS "MEDIAN_rpc_remove_requested_per_second", MAX("rpc_remove_requested_per_second") AS "MAX_rpc_remove_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_rmdir_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_rmdir_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_rmdir_latency_seconds_per_op") AS "MIN_rpc_rmdir_latency_seconds_per_op", MEAN("rpc_rmdir_latency_seconds_per_op") AS "MEAN_rpc_rmdir_latency_seconds_per_op", MEDIAN("rpc_rmdir_latency_seconds_per_op") AS "MEDIAN_rpc_rmdir_latency_seconds_per_op", MAX("rpc_rmdir_latency_seconds_per_op") AS "MAX_rpc_rmdir_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_rmdir_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_rmdir_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_rmdir_requested_per_second") AS "MIN_rpc_rmdir_requested_per_second", MEAN("rpc_rmdir_requested_per_second") AS "MEAN_rpc_rmdir_requested_per_second", MEDIAN("rpc_rmdir_requested_per_second") AS "MEDIAN_rpc_rmdir_requested_per_second", MAX("rpc_rmdir_requested_per_second") AS "MAX_rpc_rmdir_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_write_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_write_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("rpc_write_latency_seconds_per_op") AS "MIN_rpc_write_latency_seconds_per_op", MEAN("rpc_write_latency_seconds_per_op") AS "MEAN_rpc_write_latency_seconds_per_op", MEDIAN("rpc_write_latency_seconds_per_op") AS "MEDIAN_rpc_write_latency_seconds_per_op", MAX("rpc_write_latency_seconds_per_op") AS "MAX_rpc_write_latency_seconds_per_op" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
DROP CONTINUOUS QUERY "history.io_mount_nfs_rpc_write_requested_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.io_mount_nfs_rpc_write_requested_per_second" ON "gustat" BEGIN SELECT MIN("rpc_write_requested_per_second") AS "MIN_rpc_write_requested_per_second", MEAN("rpc_write_requested_per_second") AS "MEAN_rpc_write_requested_per_second", MEDIAN("rpc_write_requested_per_second") AS "MEDIAN_rpc_write_requested_per_second", MAX("rpc_write_requested_per_second") AS "MAX_rpc_write_requested_per_second" INTO "gustat"."history"."io_mount_nfs" FROM "gustat"."temporary"."io_mount_nfs" GROUP BY time(1d),"path" END;
__EOF__



# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.mem_info_available_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_available_bytes" ON "gustat" BEGIN SELECT MIN("available_bytes") AS "MIN_available_bytes", MEAN("available_bytes") AS "MEAN_available_bytes", MEDIAN("available_bytes") AS "MEDIAN_available_bytes", MAX("available_bytes") AS "MAX_available_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_buffer_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_buffer_bytes" ON "gustat" BEGIN SELECT MIN("buffer_bytes") AS "MIN_buffer_bytes", MEAN("buffer_bytes") AS "MEAN_buffer_bytes", MEDIAN("buffer_bytes") AS "MEDIAN_buffer_bytes", MAX("buffer_bytes") AS "MAX_buffer_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_cache_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_cache_bytes" ON "gustat" BEGIN SELECT MIN("cache_bytes") AS "MIN_cache_bytes", MEAN("cache_bytes") AS "MEAN_cache_bytes", MEDIAN("cache_bytes") AS "MEDIAN_cache_bytes", MAX("cache_bytes") AS "MAX_cache_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_free_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_free_bytes" ON "gustat" BEGIN SELECT MIN("free_bytes") AS "MIN_free_bytes", MEAN("free_bytes") AS "MEAN_free_bytes", MEDIAN("free_bytes") AS "MEDIAN_free_bytes", MAX("free_bytes") AS "MAX_free_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_mapped_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_mapped_bytes" ON "gustat" BEGIN SELECT MIN("mapped_bytes") AS "MIN_mapped_bytes", MEAN("mapped_bytes") AS "MEAN_mapped_bytes", MEDIAN("mapped_bytes") AS "MEDIAN_mapped_bytes", MAX("mapped_bytes") AS "MAX_mapped_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_shared_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_shared_bytes" ON "gustat" BEGIN SELECT MIN("shared_bytes") AS "MIN_shared_bytes", MEAN("shared_bytes") AS "MEAN_shared_bytes", MEDIAN("shared_bytes") AS "MEDIAN_shared_bytes", MAX("shared_bytes") AS "MAX_shared_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_slab_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_slab_bytes" ON "gustat" BEGIN SELECT MIN("slab_bytes") AS "MIN_slab_bytes", MEAN("slab_bytes") AS "MEAN_slab_bytes", MEDIAN("slab_bytes") AS "MEDIAN_slab_bytes", MAX("slab_bytes") AS "MAX_slab_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_swap_free_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_swap_free_bytes" ON "gustat" BEGIN SELECT MIN("swap_free_bytes") AS "MIN_swap_free_bytes", MEAN("swap_free_bytes") AS "MEAN_swap_free_bytes", MEDIAN("swap_free_bytes") AS "MEDIAN_swap_free_bytes", MAX("swap_free_bytes") AS "MAX_swap_free_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_swap_total_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_swap_total_bytes" ON "gustat" BEGIN SELECT MIN("swap_total_bytes") AS "MIN_swap_total_bytes", MEAN("swap_total_bytes") AS "MEAN_swap_total_bytes", MEDIAN("swap_total_bytes") AS "MEDIAN_swap_total_bytes", MAX("swap_total_bytes") AS "MAX_swap_total_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.mem_info_total_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.mem_info_total_bytes" ON "gustat" BEGIN SELECT MIN("total_bytes") AS "MIN_total_bytes", MEAN("total_bytes") AS "MEAN_total_bytes", MEDIAN("total_bytes") AS "MEDIAN_total_bytes", MAX("total_bytes") AS "MAX_total_bytes" INTO "gustat"."history"."mem_info" FROM "gustat"."long"."mem_info" GROUP BY time(1d),"task","serie","host" END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.net_dev" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.net_dev" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("rx_bytes"),1s) AS "rx_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("rx_dropped_packets"),1s) AS "rx_dropped_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("rx_multicasts_frames"),1s) AS "rx_multicasts_frames_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("rx_packets"),1s) AS "rx_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_bytes"),1s) AS "tx_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_dropped_packets"),1s) AS "tx_dropped_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_packets"),1s) AS "tx_packets_per_second"
INTO
  "gustat"."temporary"."net_dev"
FROM
  "gustat"."long"."net_dev"
GROUP BY
  time(5s),"task","serie","host","device"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.net_dev_rx_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_rx_bytes_per_second" ON "gustat" BEGIN SELECT MIN("rx_bytes_per_second") AS "MIN_rx_bytes_per_second", MEAN("rx_bytes_per_second") AS "MEAN_rx_bytes_per_second", MEDIAN("rx_bytes_per_second") AS "MEDIAN_rx_bytes_per_second", MAX("rx_bytes_per_second") AS "MAX_rx_bytes_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_rx_dropped_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_rx_dropped_packets_per_second" ON "gustat" BEGIN SELECT MIN("rx_dropped_packets_per_second") AS "MIN_rx_dropped_packets_per_second", MEAN("rx_dropped_packets_per_second") AS "MEAN_rx_dropped_packets_per_second", MEDIAN("rx_dropped_packets_per_second") AS "MEDIAN_rx_dropped_packets_per_second", MAX("rx_dropped_packets_per_second") AS "MAX_rx_dropped_packets_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_rx_multicasts_frames_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_rx_multicasts_frames_per_second" ON "gustat" BEGIN SELECT MIN("rx_multicasts_frames_per_second") AS "MIN_rx_multicasts_frames_per_second", MEAN("rx_multicasts_frames_per_second") AS "MEAN_rx_multicasts_frames_per_second", MEDIAN("rx_multicasts_frames_per_second") AS "MEDIAN_rx_multicasts_frames_per_second", MAX("rx_multicasts_frames_per_second") AS "MAX_rx_multicasts_frames_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_rx_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_rx_packets_per_second" ON "gustat" BEGIN SELECT MIN("rx_packets_per_second") AS "MIN_rx_packets_per_second", MEAN("rx_packets_per_second") AS "MEAN_rx_packets_per_second", MEDIAN("rx_packets_per_second") AS "MEDIAN_rx_packets_per_second", MAX("rx_packets_per_second") AS "MAX_rx_packets_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_tx_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_tx_bytes_per_second" ON "gustat" BEGIN SELECT MIN("tx_bytes_per_second") AS "MIN_tx_bytes_per_second", MEAN("tx_bytes_per_second") AS "MEAN_tx_bytes_per_second", MEDIAN("tx_bytes_per_second") AS "MEDIAN_tx_bytes_per_second", MAX("tx_bytes_per_second") AS "MAX_tx_bytes_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_tx_dropped_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_tx_dropped_packets_per_second" ON "gustat" BEGIN SELECT MIN("tx_dropped_packets_per_second") AS "MIN_tx_dropped_packets_per_second", MEAN("tx_dropped_packets_per_second") AS "MEAN_tx_dropped_packets_per_second", MEDIAN("tx_dropped_packets_per_second") AS "MEDIAN_tx_dropped_packets_per_second", MAX("tx_dropped_packets_per_second") AS "MAX_tx_dropped_packets_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.net_dev_tx_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_dev_tx_packets_per_second" ON "gustat" BEGIN SELECT MIN("tx_packets_per_second") AS "MIN_tx_packets_per_second", MEAN("tx_packets_per_second") AS "MEAN_tx_packets_per_second", MEDIAN("tx_packets_per_second") AS "MEDIAN_tx_packets_per_second", MAX("tx_packets_per_second") AS "MAX_tx_packets_per_second" INTO "gustat"."history"."net_dev" FROM "gustat"."temporary"."net_dev" GROUP BY time(1d),* END;
__EOF__



# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.net_conn_tcp4_established_count" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_conn_tcp4_established_count" ON "gustat" BEGIN SELECT MIN("tcp4_established_count") AS "MIN_tcp4_established_count", MEAN("tcp4_established_count") AS "MEAN_tcp4_established_count", MEDIAN("tcp4_established_count") AS "MEDIAN_tcp4_established_count", MAX("tcp4_established_count") AS "MAX_tcp4_established_count" INTO "gustat"."history"."net_conn" FROM "gustat"."long"."net_conn" GROUP BY time(1d),"task","serie","host" END;
DROP CONTINUOUS QUERY "history.net_conn_tcp6_established_count" ON "gustat"; CREATE CONTINUOUS QUERY "history.net_conn_tcp6_established_count" ON "gustat" BEGIN SELECT MIN("tcp6_established_count") AS "MIN_tcp6_established_count", MEAN("tcp6_established_count") AS "MEAN_tcp6_established_count", MEDIAN("tcp6_established_count") AS "MEDIAN_tcp6_established_count", MAX("tcp6_established_count") AS "MAX_tcp6_established_count" INTO "gustat"."history"."net_conn" FROM "gustat"."long"."net_conn" GROUP BY time(1d),"task","serie","host" END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.proc_stat" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.proc_stat" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("cpu_gtime_seconds"),1s) AS "cpu_gtime_load"
, NON_NEGATIVE_DERIVATIVE(LAST("cpu_stime_seconds"),1s) AS "cpu_stime_load"
, NON_NEGATIVE_DERIVATIVE(LAST("cpu_utime_seconds"),1s) AS "cpu_utime_load"
, NON_NEGATIVE_DERIVATIVE(LAST("io_reads_bytes"),1s) AS "io_reads_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_reads_chars"),1s) AS "io_reads_chars_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_reads_syscalls_count"),1s) AS "io_reads_syscalls_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_writes_bytes"),1s) AS "io_writes_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_writes_chars"),1s) AS "io_writes_chars_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("io_writes_syscalls_count"),1s) AS "io_writes_syscalls_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("mem_majflt_count"),1s) AS "mem_majflt_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("mem_minflt_count"),1s) AS "mem_minflt_per_second"
, LAST("mem_rss_bytes") AS "mem_rss_bytes"
, LAST("mem_vsize_bytes") AS "mem_vsize_bytes"
, NON_NEGATIVE_DERIVATIVE(LAST("sched_ctxt_nonvol_switches_count"),1s) AS "sched_ctxt_nonvol_switches_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("sched_ctxt_vol_switches_count"),1s) AS "sched_ctxt_vol_switches_per_second"
INTO
  "gustat"."temporary"."proc_stat"
FROM
  "gustat"."short"."proc_stat"
GROUP BY
  time(60s),"host","pid","user_uid_real"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.proc_stat_cpu_gtime_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_cpu_gtime_load" ON "gustat" BEGIN SELECT MIN("cpu_gtime_load") AS "MIN_cpu_gtime_load", MEAN("cpu_gtime_load") AS "MEAN_cpu_gtime_load", MEDIAN("cpu_gtime_load") AS "MEDIAN_cpu_gtime_load", MAX("cpu_gtime_load") AS "MAX_cpu_gtime_load" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_cpu_stime_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_cpu_stime_load" ON "gustat" BEGIN SELECT MIN("cpu_stime_load") AS "MIN_cpu_stime_load", MEAN("cpu_stime_load") AS "MEAN_cpu_stime_load", MEDIAN("cpu_stime_load") AS "MEDIAN_cpu_stime_load", MAX("cpu_stime_load") AS "MAX_cpu_stime_load" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_cpu_utime_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_cpu_utime_load" ON "gustat" BEGIN SELECT MIN("cpu_utime_load") AS "MIN_cpu_utime_load", MEAN("cpu_utime_load") AS "MEAN_cpu_utime_load", MEDIAN("cpu_utime_load") AS "MEDIAN_cpu_utime_load", MAX("cpu_utime_load") AS "MAX_cpu_utime_load" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_reads_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_reads_bytes_per_second" ON "gustat" BEGIN SELECT MIN("io_reads_bytes_per_second") AS "MIN_io_reads_bytes_per_second", MEAN("io_reads_bytes_per_second") AS "MEAN_io_reads_bytes_per_second", MEDIAN("io_reads_bytes_per_second") AS "MEDIAN_io_reads_bytes_per_second", MAX("io_reads_bytes_per_second") AS "MAX_io_reads_bytes_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_reads_chars_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_reads_chars_per_second" ON "gustat" BEGIN SELECT MIN("io_reads_chars_per_second") AS "MIN_io_reads_chars_per_second", MEAN("io_reads_chars_per_second") AS "MEAN_io_reads_chars_per_second", MEDIAN("io_reads_chars_per_second") AS "MEDIAN_io_reads_chars_per_second", MAX("io_reads_chars_per_second") AS "MAX_io_reads_chars_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_reads_syscalls_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_reads_syscalls_per_second" ON "gustat" BEGIN SELECT MIN("io_reads_syscalls_per_second") AS "MIN_io_reads_syscalls_per_second", MEAN("io_reads_syscalls_per_second") AS "MEAN_io_reads_syscalls_per_second", MEDIAN("io_reads_syscalls_per_second") AS "MEDIAN_io_reads_syscalls_per_second", MAX("io_reads_syscalls_per_second") AS "MAX_io_reads_syscalls_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_writes_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_writes_bytes_per_second" ON "gustat" BEGIN SELECT MIN("io_writes_bytes_per_second") AS "MIN_io_writes_bytes_per_second", MEAN("io_writes_bytes_per_second") AS "MEAN_io_writes_bytes_per_second", MEDIAN("io_writes_bytes_per_second") AS "MEDIAN_io_writes_bytes_per_second", MAX("io_writes_bytes_per_second") AS "MAX_io_writes_bytes_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_writes_chars_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_writes_chars_per_second" ON "gustat" BEGIN SELECT MIN("io_writes_chars_per_second") AS "MIN_io_writes_chars_per_second", MEAN("io_writes_chars_per_second") AS "MEAN_io_writes_chars_per_second", MEDIAN("io_writes_chars_per_second") AS "MEDIAN_io_writes_chars_per_second", MAX("io_writes_chars_per_second") AS "MAX_io_writes_chars_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_io_writes_syscalls_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_io_writes_syscalls_per_second" ON "gustat" BEGIN SELECT MIN("io_writes_syscalls_per_second") AS "MIN_io_writes_syscalls_per_second", MEAN("io_writes_syscalls_per_second") AS "MEAN_io_writes_syscalls_per_second", MEDIAN("io_writes_syscalls_per_second") AS "MEDIAN_io_writes_syscalls_per_second", MAX("io_writes_syscalls_per_second") AS "MAX_io_writes_syscalls_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_mem_majflt_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_mem_majflt_per_second" ON "gustat" BEGIN SELECT MIN("mem_majflt_per_second") AS "MIN_mem_majflt_per_second", MEAN("mem_majflt_per_second") AS "MEAN_mem_majflt_per_second", MEDIAN("mem_majflt_per_second") AS "MEDIAN_mem_majflt_per_second", MAX("mem_majflt_per_second") AS "MAX_mem_majflt_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_mem_minflt_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_mem_minflt_per_second" ON "gustat" BEGIN SELECT MIN("mem_minflt_per_second") AS "MIN_mem_minflt_per_second", MEAN("mem_minflt_per_second") AS "MEAN_mem_minflt_per_second", MEDIAN("mem_minflt_per_second") AS "MEDIAN_mem_minflt_per_second", MAX("mem_minflt_per_second") AS "MAX_mem_minflt_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_mem_rss_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_mem_rss_bytes" ON "gustat" BEGIN SELECT MIN("mem_rss_bytes") AS "MIN_mem_rss_bytes", MEAN("mem_rss_bytes") AS "MEAN_mem_rss_bytes", MEDIAN("mem_rss_bytes") AS "MEDIAN_mem_rss_bytes", MAX("mem_rss_bytes") AS "MAX_mem_rss_bytes" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_mem_vsize_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_mem_vsize_bytes" ON "gustat" BEGIN SELECT MIN("mem_vsize_bytes") AS "MIN_mem_vsize_bytes", MEAN("mem_vsize_bytes") AS "MEAN_mem_vsize_bytes", MEDIAN("mem_vsize_bytes") AS "MEDIAN_mem_vsize_bytes", MAX("mem_vsize_bytes") AS "MAX_mem_vsize_bytes" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_sched_ctxt_nonvol_switches_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_sched_ctxt_nonvol_switches_per_second" ON "gustat" BEGIN SELECT MIN("sched_ctxt_nonvol_switches_per_second") AS "MIN_sched_ctxt_nonvol_switches_per_second", MEAN("sched_ctxt_nonvol_switches_per_second") AS "MEAN_sched_ctxt_nonvol_switches_per_second", MEDIAN("sched_ctxt_nonvol_switches_per_second") AS "MEDIAN_sched_ctxt_nonvol_switches_per_second", MAX("sched_ctxt_nonvol_switches_per_second") AS "MAX_sched_ctxt_nonvol_switches_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
DROP CONTINUOUS QUERY "history.proc_stat_sched_ctxt_vol_switches_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.proc_stat_sched_ctxt_vol_switches_per_second" ON "gustat" BEGIN SELECT MIN("sched_ctxt_vol_switches_per_second") AS "MIN_sched_ctxt_vol_switches_per_second", MEAN("sched_ctxt_vol_switches_per_second") AS "MEAN_sched_ctxt_vol_switches_per_second", MEDIAN("sched_ctxt_vol_switches_per_second") AS "MEDIAN_sched_ctxt_vol_switches_per_second", MAX("sched_ctxt_vol_switches_per_second") AS "MAX_sched_ctxt_vol_switches_per_second" INTO "gustat"."history"."proc_stat" FROM "gustat"."temporary"."proc_stat" GROUP BY time(1d),"user_uid_real" END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.virt_cpu" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.virt_cpu" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("system_seconds"),1s) AS "system_load"
, NON_NEGATIVE_DERIVATIVE(LAST("total_seconds"),1s) AS "total_load"
, NON_NEGATIVE_DERIVATIVE(LAST("user_seconds"),1s) AS "user_load"
, LAST("vcpu_count") AS "vcpu_count"
INTO
  "gustat"."temporary"."virt_cpu"
FROM
  "gustat"."long"."virt_cpu"
GROUP BY
  time(60s),"guest"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.virt_cpu_system_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_cpu_system_load" ON "gustat" BEGIN SELECT MIN("system_load") AS "MIN_system_load", MEAN("system_load") AS "MEAN_system_load", MEDIAN("system_load") AS "MEDIAN_system_load", MAX("system_load") AS "MAX_system_load" INTO "gustat"."history"."virt_cpu" FROM "gustat"."temporary"."virt_cpu" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_cpu_total_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_cpu_total_load" ON "gustat" BEGIN SELECT MIN("total_load") AS "MIN_total_load", MEAN("total_load") AS "MEAN_total_load", MEDIAN("total_load") AS "MEDIAN_total_load", MAX("total_load") AS "MAX_total_load" INTO "gustat"."history"."virt_cpu" FROM "gustat"."temporary"."virt_cpu" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_cpu_user_load" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_cpu_user_load" ON "gustat" BEGIN SELECT MIN("user_load") AS "MIN_user_load", MEAN("user_load") AS "MEAN_user_load", MEDIAN("user_load") AS "MEDIAN_user_load", MAX("user_load") AS "MAX_user_load" INTO "gustat"."history"."virt_cpu" FROM "gustat"."temporary"."virt_cpu" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_cpu_vcpu_count" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_cpu_vcpu_count" ON "gustat" BEGIN SELECT MIN("vcpu_count") AS "MIN_vcpu_count", MEAN("vcpu_count") AS "MEAN_vcpu_count", MEDIAN("vcpu_count") AS "MEDIAN_vcpu_count", MAX("vcpu_count") AS "MAX_vcpu_count" INTO "gustat"."history"."virt_cpu" FROM "gustat"."temporary"."virt_cpu" GROUP BY time(1d),* END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.virt_io" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.virt_io" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("reads_bytes"),1s) AS "reads_bytes_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("reads_elapsed_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("reads_ops_count")) AS "reads_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("reads_ops_count"),1s) AS "reads_ops_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("writes_bytes"),1s) AS "writes_bytes_per_second"
, NON_NEGATIVE_DIFFERENCE(LAST("writes_elapsed_seconds"))/NON_NEGATIVE_DIFFERENCE(LAST("writes_ops_count")) AS "writes_latency_seconds_per_op"
, NON_NEGATIVE_DERIVATIVE(LAST("writes_ops_count"),1s) AS "writes_ops_per_second"
INTO
  "gustat"."temporary"."virt_io"
FROM
  "gustat"."long"."virt_io"
GROUP BY
  time(60s),"guest","devid"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.virt_io_reads_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_reads_bytes_per_second" ON "gustat" BEGIN SELECT MIN("reads_bytes_per_second") AS "MIN_reads_bytes_per_second", MEAN("reads_bytes_per_second") AS "MEAN_reads_bytes_per_second", MEDIAN("reads_bytes_per_second") AS "MEDIAN_reads_bytes_per_second", MAX("reads_bytes_per_second") AS "MAX_reads_bytes_per_second" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_io_reads_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_reads_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("reads_latency_seconds_per_op") AS "MIN_reads_latency_seconds_per_op", MEAN("reads_latency_seconds_per_op") AS "MEAN_reads_latency_seconds_per_op", MEDIAN("reads_latency_seconds_per_op") AS "MEDIAN_reads_latency_seconds_per_op", MAX("reads_latency_seconds_per_op") AS "MAX_reads_latency_seconds_per_op" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_io_reads_ops_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_reads_ops_per_second" ON "gustat" BEGIN SELECT MIN("reads_ops_per_second") AS "MIN_reads_ops_per_second", MEAN("reads_ops_per_second") AS "MEAN_reads_ops_per_second", MEDIAN("reads_ops_per_second") AS "MEDIAN_reads_ops_per_second", MAX("reads_ops_per_second") AS "MAX_reads_ops_per_second" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_io_writes_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_writes_bytes_per_second" ON "gustat" BEGIN SELECT MIN("writes_bytes_per_second") AS "MIN_writes_bytes_per_second", MEAN("writes_bytes_per_second") AS "MEAN_writes_bytes_per_second", MEDIAN("writes_bytes_per_second") AS "MEDIAN_writes_bytes_per_second", MAX("writes_bytes_per_second") AS "MAX_writes_bytes_per_second" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_io_writes_latency_seconds_per_op" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_writes_latency_seconds_per_op" ON "gustat" BEGIN SELECT MIN("writes_latency_seconds_per_op") AS "MIN_writes_latency_seconds_per_op", MEAN("writes_latency_seconds_per_op") AS "MEAN_writes_latency_seconds_per_op", MEDIAN("writes_latency_seconds_per_op") AS "MEDIAN_writes_latency_seconds_per_op", MAX("writes_latency_seconds_per_op") AS "MAX_writes_latency_seconds_per_op" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_io_writes_ops_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_io_writes_ops_per_second" ON "gustat" BEGIN SELECT MIN("writes_ops_per_second") AS "MIN_writes_ops_per_second", MEAN("writes_ops_per_second") AS "MEAN_writes_ops_per_second", MEDIAN("writes_ops_per_second") AS "MEDIAN_writes_ops_per_second", MAX("writes_ops_per_second") AS "MAX_writes_ops_per_second" INTO "gustat"."history"."virt_io" FROM "gustat"."temporary"."virt_io" GROUP BY time(1d),* END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.virt_mem" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.virt_mem" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  LAST("available_bytes") AS "available_bytes"
, LAST("current_bytes") AS "current_bytes"
, NON_NEGATIVE_DERIVATIVE(LAST("majflt_count"),1s) AS "majflt_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("minflt_count"),1s) AS "minflt_per_second"
, LAST("rss_bytes") AS "rss_bytes"
, NON_NEGATIVE_DERIVATIVE(LAST("swap_reads_bytes"),1s) AS "swap_reads_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("swap_writes_bytes"),1s) AS "swap_writes_bytes_per_second"
, LAST("unused_bytes") AS "unused_bytes"
INTO
  "gustat"."temporary"."virt_mem"
FROM
  "gustat"."long"."virt_mem"
GROUP BY
  time(60s),"guest"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.virt_mem_available_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_available_bytes" ON "gustat" BEGIN SELECT MIN("available_bytes") AS "MIN_available_bytes", MEAN("available_bytes") AS "MEAN_available_bytes", MEDIAN("available_bytes") AS "MEDIAN_available_bytes", MAX("available_bytes") AS "MAX_available_bytes" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_current_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_current_bytes" ON "gustat" BEGIN SELECT MIN("current_bytes") AS "MIN_current_bytes", MEAN("current_bytes") AS "MEAN_current_bytes", MEDIAN("current_bytes") AS "MEDIAN_current_bytes", MAX("current_bytes") AS "MAX_current_bytes" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_majflt_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_majflt_per_second" ON "gustat" BEGIN SELECT MIN("majflt_per_second") AS "MIN_majflt_per_second", MEAN("majflt_per_second") AS "MEAN_majflt_per_second", MEDIAN("majflt_per_second") AS "MEDIAN_majflt_per_second", MAX("majflt_per_second") AS "MAX_majflt_per_second" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_minflt_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_minflt_per_second" ON "gustat" BEGIN SELECT MIN("minflt_per_second") AS "MIN_minflt_per_second", MEAN("minflt_per_second") AS "MEAN_minflt_per_second", MEDIAN("minflt_per_second") AS "MEDIAN_minflt_per_second", MAX("minflt_per_second") AS "MAX_minflt_per_second" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_rss_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_rss_bytes" ON "gustat" BEGIN SELECT MIN("rss_bytes") AS "MIN_rss_bytes", MEAN("rss_bytes") AS "MEAN_rss_bytes", MEDIAN("rss_bytes") AS "MEDIAN_rss_bytes", MAX("rss_bytes") AS "MAX_rss_bytes" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_swap_reads_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_swap_reads_bytes_per_second" ON "gustat" BEGIN SELECT MIN("swap_reads_bytes_per_second") AS "MIN_swap_reads_bytes_per_second", MEAN("swap_reads_bytes_per_second") AS "MEAN_swap_reads_bytes_per_second", MEDIAN("swap_reads_bytes_per_second") AS "MEDIAN_swap_reads_bytes_per_second", MAX("swap_reads_bytes_per_second") AS "MAX_swap_reads_bytes_per_second" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_swap_writes_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_swap_writes_bytes_per_second" ON "gustat" BEGIN SELECT MIN("swap_writes_bytes_per_second") AS "MIN_swap_writes_bytes_per_second", MEAN("swap_writes_bytes_per_second") AS "MEAN_swap_writes_bytes_per_second", MEDIAN("swap_writes_bytes_per_second") AS "MEDIAN_swap_writes_bytes_per_second", MAX("swap_writes_bytes_per_second") AS "MAX_swap_writes_bytes_per_second" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_mem_unused_bytes" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_mem_unused_bytes" ON "gustat" BEGIN SELECT MIN("unused_bytes") AS "MIN_unused_bytes", MEAN("unused_bytes") AS "MEAN_unused_bytes", MEDIAN("unused_bytes") AS "MEDIAN_unused_bytes", MAX("unused_bytes") AS "MAX_unused_bytes" INTO "gustat"."history"."virt_mem" FROM "gustat"."temporary"."virt_mem" GROUP BY time(1d),* END;
__EOF__



:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "temporary.virt_net" ON "gustat";
CREATE CONTINUOUS QUERY "temporary.virt_net" ON "gustat"
RESAMPLE EVERY 15m FOR 20m
BEGIN
SELECT
  NON_NEGATIVE_DERIVATIVE(LAST("rx_bytes"),1s) AS "rx_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("rx_dropped_packets"),1s) AS "rx_dropped_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("rx_packets"),1s) AS "rx_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_bytes"),1s) AS "tx_bytes_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_dropped_packets"),1s) AS "tx_dropped_packets_per_second"
, NON_NEGATIVE_DERIVATIVE(LAST("tx_packets"),1s) AS "tx_packets_per_second"
INTO
  "gustat"."temporary"."virt_net"
FROM
  "gustat"."long"."virt_net"
GROUP BY
  time(60s),"guest","devid"
END
;
__EOF__

# WARNING: history CQs MUST be split to limit heap memory usage
:; cat << __EOF__ | tr '\n' ' ' | sed 's/; */;\n/g' | influx -database gustat
DROP CONTINUOUS QUERY "history.virt_net_rx_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_rx_bytes_per_second" ON "gustat" BEGIN SELECT MIN("rx_bytes_per_second") AS "MIN_rx_bytes_per_second", MEAN("rx_bytes_per_second") AS "MEAN_rx_bytes_per_second", MEDIAN("rx_bytes_per_second") AS "MEDIAN_rx_bytes_per_second", MAX("rx_bytes_per_second") AS "MAX_rx_bytes_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_net_rx_dropped_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_rx_dropped_packets_per_second" ON "gustat" BEGIN SELECT MIN("rx_dropped_packets_per_second") AS "MIN_rx_dropped_packets_per_second", MEAN("rx_dropped_packets_per_second") AS "MEAN_rx_dropped_packets_per_second", MEDIAN("rx_dropped_packets_per_second") AS "MEDIAN_rx_dropped_packets_per_second", MAX("rx_dropped_packets_per_second") AS "MAX_rx_dropped_packets_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_net_rx_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_rx_packets_per_second" ON "gustat" BEGIN SELECT MIN("rx_packets_per_second") AS "MIN_rx_packets_per_second", MEAN("rx_packets_per_second") AS "MEAN_rx_packets_per_second", MEDIAN("rx_packets_per_second") AS "MEDIAN_rx_packets_per_second", MAX("rx_packets_per_second") AS "MAX_rx_packets_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_net_tx_bytes_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_tx_bytes_per_second" ON "gustat" BEGIN SELECT MIN("tx_bytes_per_second") AS "MIN_tx_bytes_per_second", MEAN("tx_bytes_per_second") AS "MEAN_tx_bytes_per_second", MEDIAN("tx_bytes_per_second") AS "MEDIAN_tx_bytes_per_second", MAX("tx_bytes_per_second") AS "MAX_tx_bytes_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_net_tx_dropped_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_tx_dropped_packets_per_second" ON "gustat" BEGIN SELECT MIN("tx_dropped_packets_per_second") AS "MIN_tx_dropped_packets_per_second", MEAN("tx_dropped_packets_per_second") AS "MEAN_tx_dropped_packets_per_second", MEDIAN("tx_dropped_packets_per_second") AS "MEDIAN_tx_dropped_packets_per_second", MAX("tx_dropped_packets_per_second") AS "MAX_tx_dropped_packets_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
DROP CONTINUOUS QUERY "history.virt_net_tx_packets_per_second" ON "gustat"; CREATE CONTINUOUS QUERY "history.virt_net_tx_packets_per_second" ON "gustat" BEGIN SELECT MIN("tx_packets_per_second") AS "MIN_tx_packets_per_second", MEAN("tx_packets_per_second") AS "MEAN_tx_packets_per_second", MEDIAN("tx_packets_per_second") AS "MEDIAN_tx_packets_per_second", MAX("tx_packets_per_second") AS "MAX_tx_packets_per_second" INTO "gustat"."history"."virt_net" FROM "gustat"."temporary"."virt_net" GROUP BY time(1d),* END;
__EOF__
