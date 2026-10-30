"""Write variants/<name>.py = ../trader.py with named module constants overridden.

usage: python make_variant.py <name> CONST=value [CONST=value ...]
"""

import re
import sys
from pathlib import Path

here = Path(__file__).parent
name, overrides = sys.argv[1], sys.argv[2:]
source = (here.parent / "trader.py").read_text()
for item in overrides:
    const, value = item.split("=", 1)
    pattern = rf"^{const} = .*$"
    if not re.search(pattern, source, flags=re.M):
        raise SystemExit(f"{const} not found")
    source = re.sub(pattern, f"{const} = {value}  # variant override", source, count=1, flags=re.M)
(here / f"{name}.py").write_text(f"# variant {name}: {' '.join(overrides)}\n" + source)
