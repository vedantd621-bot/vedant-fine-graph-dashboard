#!/usr/bin/env python3
"""
FinGraph Phase 1 Structure Verification Script
Verifies presence and basic integrity of repository scaffold, configuration, and documentation.
"""
import os
import sys
from pathlib import Path

REQUIRED_DIRS = [
    "simulator/src",
    "simulator/tests",
    "flink/src",
    "flink/tests",
    "neo4j/constraints",
    "neo4j/indexes",
    "neo4j/cypher",
    "neo4j/gds",
    "neo4j/seed",
    "backend/app",
    "backend/tests",
    "dashboard/src",
    "dashboard/public",
    "alerts/src",
    "alerts/tests",
    "tests/integration",
    "tests/performance",
    "tests/e2e",
    "docs/architecture",
    "docs/performance",
    "docs/demo",
    "docs/risk",
    "docs/security",
]

REQUIRED_FILES = [
    ".gitignore",
    ".env.example",
    "LICENSE",
    "README.md",
    "docker-compose.yml",
    "simulator/README.md",
    "simulator/requirements.txt",
    "flink/README.md",
    "flink/requirements.txt",
    "neo4j/README.md",
    "neo4j/constraints/01_constraints.cypher",
    "neo4j/indexes/01_indexes.cypher",
    "neo4j/cypher/01_queries.cypher",
    "neo4j/gds/01_gds_projections.cypher",
    "neo4j/seed/01_seed_graph.cypher",
    "backend/README.md",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "dashboard/README.md",
    "dashboard/package.json",
    "dashboard/Dockerfile",
    "alerts/README.md",
    "alerts/requirements.txt",
    "docs/architecture/system-architecture.md",
    "docs/architecture/data-model.md",
    "docs/architecture/data-flow.md",
    "docs/architecture/health-checks.md",
    "docs/performance/latency-report.md",
    "docs/performance/query-performance.md",
    "docs/demo/demo-script.md",
    "docs/demo/test-scenarios.md",
    "docs/risk/risk-scoring.md",
    "docs/security/security.md",
    "docs/PROJECT_STATUS.md",
]

def main():
    root = Path(__file__).resolve().parent
    print(f"[*] Verifying FinGraph Repository Structure at: {root}\n")

    errors = []
    
    # 1. Check directories
    print("[1/3] Checking directory structure...")
    for d in REQUIRED_DIRS:
        dp = root / d
        if not dp.is_dir():
            errors.append(f"Missing directory: {d}")
        else:
            print(f"  [OK] Directory: {d}")

    # 2. Check files
    print("\n[2/3] Checking required files...")
    for f in REQUIRED_FILES:
        fp = root / f
        if not fp.is_file():
            errors.append(f"Missing file: {f}")
        else:
            size = fp.stat().st_size
            print(f"  [OK] File ({size} bytes): {f}")

    # 3. Check docker-compose services
    print("\n[3/3] Checking docker-compose services...")
    dc_file = root / "docker-compose.yml"
    if dc_file.is_file():
        content = dc_file.read_text()
        required_services = ["kafka:", "neo4j:", "flink-jobmanager:", "backend:", "dashboard:"]
        for s in required_services:
            if s in content:
                print(f"  [OK] Service defined: {s[:-1]}")
            else:
                errors.append(f"docker-compose.yml missing service definition: {s}")

    print("\n" + "="*60)
    if errors:
        print(f"[FAIL] Found {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[SUCCESS] Phase 1 Structure & Foundation verification PASSED!")
        print("="*60)

if __name__ == "__main__":
    main()
