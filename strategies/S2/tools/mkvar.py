"""Make variants/<name>.py = trader.py + override lines (module globals are read at call time).
    python tools/mkvar.py name 'SOFT_C = 20' 'CONFIG["pink"] = False'
"""
import sys
from pathlib import Path
here = Path(__file__).resolve().parents[1]
name, *lines = sys.argv[1:]
src = (here / "trader.py").read_text()
(here / "variants" / f"{name}.py").write_text(src + "\n\n# ---- variant overrides\n" + "\n".join(lines) + "\n")
print(here / "variants" / f"{name}.py")
