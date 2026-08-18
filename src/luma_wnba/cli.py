"""luma-wnba top 2026 / luma-wnba fetch 2026 / luma-wnba seasons / luma-wnba cache --clear"""

import argparse
import sys

from . import (
    load_stints,
    load_crosswalk,
    player_seconds,
    seasons,
    cache_dir,
    clear_cache,
    __version__,
)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="luma-wnba", description="LUMA WNBA stint data")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="cmd")

    top_parser = subparsers.add_parser("top")
    top_parser.add_argument("season", type=int)
    top_parser.add_argument("--kind", default="rs", choices=["rs", "po"])
    top_parser.add_argument("--n", type=int, default=10)
    top_parser.add_argument("--ref", default="main")
    top_parser.add_argument("--source", default="auto", choices=["auto", "local", "remote"])

    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("season", type=int)
    fetch_parser.add_argument("--kind", default="rs")
    fetch_parser.add_argument("--ref", default="main")

    subparsers.add_parser("seasons")

    cache_parser = subparsers.add_parser("cache")
    cache_parser.add_argument("--clear", action="store_true")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "top":
            games = load_stints(args.season, args.kind, source=args.source, ref=args.ref)
            cw = load_crosswalk(source=args.source, ref=args.ref)
            secs = player_seconds(games)
            sorted_pids = sorted(secs.items(), key=lambda x: x[1], reverse=True)
            kind_label = "regular season" if args.kind == "rs" else "playoffs"
            print(f"WNBA {args.season} {kind_label} - minutes leaders")
            for i, (pid, total_secs) in enumerate(sorted_pids[: args.n], 1):
                name = cw.get(pid, {}).get("display_name", pid)
                print(f"{i:2d}. {name:<24s} {total_secs / 60:7.1f}")

        elif args.cmd == "fetch":
            games = load_stints(args.season, args.kind, source="remote", ref=args.ref)
            print(f"downloaded {len(games)} games")
            print(cache_dir(args.ref))

        elif args.cmd == "seasons":
            rs_seasons = seasons("rs")
            po_seasons = seasons("po")
            print(f"rs {min(rs_seasons)}-{max(rs_seasons)}")
            print(f"po {min(po_seasons)}-{max(po_seasons)}")

        elif args.cmd == "cache":
            if args.clear:
                path = clear_cache()
                print(f"cleared {path}")
            else:
                print(cache_dir())

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"luma-wnba: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())