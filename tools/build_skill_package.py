#!/usr/bin/env python3
"""Build a deterministic, runtime-free Agent Skill archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "chanlun-trading-system"
REQUIRED = (
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("scripts/skill_workbench.py"),
)


def source_files() -> list[Path]:
    files = list(REQUIRED)
    files.extend(path.relative_to(ROOT) for path in sorted((ROOT / "references").glob("*.md")))
    missing = [str(path) for path in files if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError("missing Skill source: {}".format(", ".join(missing)))
    return sorted(files, key=lambda path: path.as_posix())


def write_archive(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "{}-skill.zip".format(SKILL_NAME)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in source_files():
            info = ZipInfo("{}/{}".format(SKILL_NAME, relative.as_posix()))
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if relative.suffix == ".py" else 0o644) << 16
            archive.writestr(info, (ROOT / relative).read_bytes())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    output = write_archive(args.output_dir.resolve())
    print(json.dumps({"artifact": output.name, "files": len(source_files())}, sort_keys=True))


if __name__ == "__main__":
    main()
