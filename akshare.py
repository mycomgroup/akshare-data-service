import sys
from pathlib import Path

_src = Path(__file__).parent / "akshare"
if _src.is_dir():
    sys.path.insert(0, str(_src))
    if "akshare" in sys.modules:
        del sys.modules["akshare"]
    import importlib
    importlib.import_module("akshare")
