"""
FinGraph Neo4j Database Client.
Provides a robust, pooled Python driver client for executing parameterized Cypher queries,
schema migrations, and transactional batch upserts.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from neo4j import GraphDatabase, Driver, Session, exceptions as neo4j_exceptions
except ImportError:
    GraphDatabase = None
    Driver = None
    Session = None
    neo4j_exceptions = None

try:
    from neo4j.src.config import Neo4jConfig, get_neo4j_config
except ImportError:
    from config import Neo4jConfig, get_neo4j_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Neo4jClient] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.Neo4jClient")


class Neo4jClient:
    """
    Enterprise-grade Neo4j database client with connection pooling,
    parameterized query execution, and session management.
    """

    def __init__(
        self,
        config: Optional[Neo4jConfig] = None,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auto_connect: bool = True,
    ):
        self.config = config or get_neo4j_config()
        self.uri = uri or self.config.uri
        self.user = user or self.config.user
        self.password = password or self.config.password
        self.database = database or self.config.database
        self.driver: Optional[Driver] = None

        if auto_connect:
            self.connect()

    def connect(self) -> None:
        """Initializes the Neo4j driver with connection pooling."""
        if GraphDatabase is None:
            raise ImportError("The 'neo4j' Python package is required. Install via requirements.txt")

        logger.info(f"Connecting to Neo4j at {self.uri} (database: {self.database})...")
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout,
            )
            logger.info("Neo4j driver initialized.")
        except Exception as exc:
            logger.error(f"Failed to initialize Neo4j driver: {exc}")
            raise ConnectionError(f"Could not connect to Neo4j at {self.uri}: {exc}") from exc

    def verify_connectivity(self) -> bool:
        """Verifies active connectivity to the Neo4j cluster."""
        if not self.driver:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.warning(f"Neo4j connectivity check failed: {exc}")
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a read Cypher query using managed sessions.
        Returns a list of dict records.
        """
        if not self.driver:
            raise ConnectionError("Neo4j driver is not connected. Call connect() first.")

        db = database or self.database
        params = parameters or {}

        try:
            with self.driver.session(database=db) as session:
                result = session.run(query, params)
                return [record.data() for record in result]
        except Exception as exc:
            logger.error(f"Cypher read execution failed: {exc}\nQuery: {query}\nParams: {params}")
            raise

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a write Cypher transaction using managed write transaction functions.
        """
        if not self.driver:
            raise ConnectionError("Neo4j driver is not connected. Call connect() first.")

        db = database or self.database
        params = parameters or {}

        def _write_tx(tx):
            result = tx.run(query, params)
            return [record.data() for record in result]

        try:
            with self.driver.session(database=db) as session:
                return session.execute_write(_write_tx)
        except Exception as exc:
            logger.error(f"Cypher write execution failed: {exc}\nQuery: {query}\nParams: {params}")
            raise

    def execute_script(self, cypher_script: str, database: Optional[str] = None) -> List[Any]:
        """
        Executes multiple semicolon-separated Cypher statements sequentially.
        Ignores comments (//) and empty blocks.
        """
        statements = []
        raw_lines = cypher_script.splitlines()
        clean_lines = []
        for line in raw_lines:
            stripped = line.strip()
            if stripped.startswith("//") or not stripped:
                continue
            clean_lines.append(line)

        full_text = "\n".join(clean_lines)
        raw_statements = [s.strip() for s in full_text.split(";") if s.strip()]

        results = []
        for stmt in raw_statements:
            res = self.execute_write(stmt, database=database)
            results.append(res)
        return results

    def close(self) -> None:
        """Closes the Neo4j driver and releases all pooled connections."""
        if self.driver:
            logger.info("Closing Neo4j driver connection...")
            self.driver.close()
            self.driver = None
            logger.info("Neo4j driver closed cleanly.")

    def __enter__(self) -> "Neo4jClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
