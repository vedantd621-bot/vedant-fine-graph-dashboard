"""
FinGraph Neo4j Module Package.
Exposes official neo4j driver symbols (GraphDatabase, Driver, Session, etc.) alongside local sub-packages.
"""
import os
import sys
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

# Re-export official neo4j driver classes so local package directory doesn't shadow them
try:
    import importlib.util
    for _p in sys.path:
        if "site-packages" in _p:
            _init_p = os.path.join(_p, "neo4j", "__init__.py")
            if os.path.isfile(_init_p) and os.path.abspath(_init_p) != os.path.abspath(__file__):
                _spec = importlib.util.spec_from_file_location("official_neo4j_driver", _init_p)
                if _spec and _spec.loader:
                    _mod = importlib.util.module_from_spec(_spec)
                    sys.modules["official_neo4j_driver"] = _mod
                    _spec.loader.exec_module(_mod)
                    for _attr in dir(_mod):
                        if not _attr.startswith("__") and _attr != "Config":
                            globals()[_attr] = getattr(_mod, _attr)
                    if hasattr(_mod, "__all__"):
                        __all__ = list(_mod.__all__) + ["src", "scripts", "seed", "constraints", "indexes", "cypher", "gds"]
                    break
except Exception:
    pass
