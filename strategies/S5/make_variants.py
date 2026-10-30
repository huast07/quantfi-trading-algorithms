"""Write variants/<name>.py (and trader.py) from src_trader.py by replacing only its CONFIG block.

Usage: python make_variants.py name key=value [key=value ...]   (one variant)
       python make_variants.py --trader name                     (copy variants/<name>.py to trader.py)
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOCK = re.compile(r"CONFIG = \{.*?\n\}\n", re.S)


def render(overrides: dict) -> str:
    source = (HERE / "src_trader.py").read_text(encoding="utf-8")
    match = BLOCK.search(source)
    config = {
        "rule": "EQ", "budget": 800.0, "half_life": 1000.0, "share_step": 0.002,
    }
    config.update(overrides)
    block = "CONFIG = " + json.dumps(config, indent=4) + "\n"
    return source[: match.start()] + block + source[match.end():]


def parse(value: str):
    try:
        return json.loads(value)
    except ValueError:
        return value


def main(argv):
    if argv[0] == "--trader":
        (HERE / "trader.py").write_text((HERE / "variants" / f"{argv[1]}.py").read_text(encoding="utf-8"))
        return
    name, pairs = argv[0], argv[1:]
    overrides = {k: parse(v) for k, v in (p.split("=", 1) for p in pairs)}
    (HERE / "variants").mkdir(exist_ok=True)
    (HERE / "variants" / f"{name}.py").write_text(render(overrides), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
