"""Legacy entry point preserved for backwards compatibility.

The ACE training logic now runs inside session2_with_ace.py.
Running this script simply informs the user about the updated workflow.
"""

from __future__ import annotations

import sys


def main() -> None:
    message = (
        "ACE training is now integrated into session2_with_ace.py.\n"
        "Run `python session2_with_ace.py` after generating baseline artifacts."
    )
    print(message)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
