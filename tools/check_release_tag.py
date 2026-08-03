#!/usr/bin/env python3
"""Fail unless a Git tag matches the Python package version."""

from __future__ import annotations

import argparse
import json

from chanlun_visual import __version__


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    expected = "v{}".format(__version__)
    if args.tag != expected:
        raise SystemExit("release tag {} does not match expected {}".format(args.tag, expected))
    print(json.dumps({"status": "pass", "tag": args.tag, "version": __version__}, sort_keys=True))


if __name__ == "__main__":
    main()
