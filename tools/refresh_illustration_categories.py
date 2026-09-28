#!/usr/bin/env python3
"""예화창고 최상위 폴더명만 읽어 config snapshot을 안전하게 갱신한다."""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.illustration_categories import main


if __name__ == "__main__":
    main()
