# FinGraph v1.0 Production Configuration Reference

## Environment Variables

| Variable | Default | Description | Environment |
| :--- | :--- | :--- | :--- |
| `API_HOST` | `0.0.0.0` | API bind address | All |
| `API_PORT` | `8000` | API listening port | All |
| `JWT_SECRET` | `change_in_production` | HMAC secret for JWT signing | Production (Required) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm | All |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token validity duration | All |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection URI | All |
| `NEO4J_USER` | `neo4j` | Database username | All |
| `NEO4J_PASSWORD` | `password` | Database password | Production (Required) |
| `NEO4J_DATABASE` | `neo4j` | Target database name | All |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker endpoints | All |
| `RATE_LIMIT_ENABLED` | `true` | Enable API rate limiting | Production |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per sliding window | Production |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Sliding window duration in seconds | Production |
