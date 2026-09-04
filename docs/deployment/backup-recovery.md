# FinGraph v1.0 Backup & Disaster Recovery Runbook

## 1. Neo4j Graph Database
* **Online Backup**: `neo4j-admin database backup --to-path=/backups/neo4j neo4j`
* **Restore**: `neo4j-admin database restore --from-path=/backups/neo4j/neo4j-backup.dump --overwrite-destination=true neo4j`
* **Verification**: Run `scripts/data_integrity_check.py` post-restore.

## 2. Kafka Topic Configurations
* **Export Offsets & Topics**: `kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups`
* **Replay DLQ**: Process events from `transactions-dlq` using recovery consumer.

## 3. Rollback Procedure
1. If a newly deployed detector version causes false positive surges, revert in Adaptive Intelligence workstation or invoke `POST /api/v1/autonomous-intelligence/recommendations/{id}/review` with `REJECTED`.
2. Revert Docker image tag to previous stable commit.
