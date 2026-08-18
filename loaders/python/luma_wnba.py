"""Deprecated path. Use the installable package instead.

    pip install luma-wnba
    import luma_wnba

This shim keeps older clone-based scripts working by loading the real package
from ../../src by file path. It is named the same as the package, so it cannot
simply import it -- the name would resolve back to this file.
"""
import os
import sys
import importlib.util

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src",
                 "luma_wnba", "__init__.py")
)

_spec = importlib.util.spec_from_file_location("_luma_wnba_pkg", _SRC)
_pkg = importlib.util.module_from_spec(_spec)
sys.modules["_luma_wnba_pkg"] = _pkg
_spec.loader.exec_module(_pkg)

# Re-export the public surface.
for _name in _pkg.__all__:
    globals()[_name] = getattr(_pkg, _name)

__all__ = list(_pkg.__all__)
__version__ = _pkg.__version__

if __name__ == "__main__":
    _games = load_stints(2026)                      # noqa: F821
    _names = load_crosswalk()                       # noqa: F821
    _secs = player_seconds(_games)                  # noqa: F821
    print("2026 regular season, minutes leaders")
    for _pid, _s in sorted(_secs.items(), key=lambda kv: -kv[1])[:10]:
        print("  %-24s %7.1f" % (_names[_pid]["display_name"], _s / 60))
