# FinGraph Disaster Recovery & Backup Procedures

## 1. Neo4j Database Backup & Recovery
### Cold Backup
`ash
docker exec -it fingraph-prod-neo4j neo4j-admin database dump neo4j --to-path=/data/backups/
`

### Restore Procedure
1. Stop running Neo4j instance:
   `ash
   docker-compose -f docker-compose.prod.yml stop neo4j
   `
2. Restore database dump:
   `ash
   docker run --rm -v neo4j_prod_data:/data -v ./backups:/backups neo4j:5.18.0 neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
   `
3. Restart Neo4j:
   `ash
   docker-compose -f docker-compose.prod.yml start neo4j
   `

## 2. Kafka Topic Disaster Recovery
- **Dead Letter Queue (DLQ)**: Malformed payloads routed to transactions_dlq.
- **Replay Mechanism**: Reset consumer group offsets:
  `ash
  kafka-consumer-groups --bootstrap-server localhost:9092 --group fingraph-realtime-api --reset-offsets --to-earliest --execute --topic transactions
  `
