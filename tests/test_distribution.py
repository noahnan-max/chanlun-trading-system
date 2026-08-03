from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

import yaml

from chanlun_visual import __version__
from chanlun_visual.diagnostics import doctor_report


ROOT = Path(__file__).resolve().parents[1]


def test_doctor_is_read_only_and_path_safe():
    report = doctor_report()
    assert report["status"] in {"pass", "pass_with_warnings"}
    assert report["version"] == __version__
    assert report["execution_allowed"] is False
    assert report["network_checked"] is False
    assert all("/Users/" not in item["detail"] for item in report["checks"])
    assert all(item["status"] != "fail" for item in report["checks"] if item["required"])


def test_cli_version_and_json_doctor():
    version = subprocess.run(
        [sys.executable, "-m", "chanlun_visual.cli", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert version.stdout.strip() == "cli.py {}".format(__version__)

    doctor = subprocess.run(
        [sys.executable, "-m", "chanlun_visual.cli", "doctor", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(doctor.stdout)["version"] == __version__


def test_skill_metadata_contract():
    skill = (ROOT / "SKILL.md").read_text()
    frontmatter = yaml.safe_load(skill.split("---", 2)[1])
    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["name"] == "chanlun-trading-system"

    metadata = yaml.safe_load((ROOT / "agents/openai.yaml").read_text())
    interface = metadata["interface"]
    assert 25 <= len(interface["short_description"]) <= 64
    assert "$chanlun-trading-system" in interface["default_prompt"]


def test_skill_archive_is_filtered_and_reproducible(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    for output_dir in (first_dir, second_dir):
        subprocess.run(
            [sys.executable, str(ROOT / "tools/build_skill_package.py"), "--output-dir", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
    first = first_dir / "chanlun-trading-system-skill.zip"
    second = second_dir / "chanlun-trading-system-skill.zip"
    first_skillhub = first_dir / "chanlun-trading-system-skillhub.zip"
    second_skillhub = second_dir / "chanlun-trading-system-skillhub.zip"
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    assert hashlib.sha256(first_skillhub.read_bytes()).digest() == hashlib.sha256(second_skillhub.read_bytes()).digest()

    with ZipFile(first) as archive:
        names = set(archive.namelist())
    prefix = "chanlun-trading-system/"
    assert prefix + "SKILL.md" in names
    assert prefix + "agents/openai.yaml" in names
    assert prefix + "scripts/skill_workbench.py" in names
    assert not any(name.startswith(prefix + "src/") for name in names)
    assert prefix + "README.md" not in names

    with ZipFile(first_skillhub) as archive:
        skillhub_frontmatter = yaml.safe_load(
            archive.read(prefix + "SKILL.md").decode("utf-8").split("---", 2)[1]
        )
    assert skillhub_frontmatter["slug"] == "chanlun-trading-system"
    assert skillhub_frontmatter["version"] == "1.1.0"
    assert skillhub_frontmatter["displayName"] == "缠论交易系统"


def test_release_tag_must_match_package_version():
    valid = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/check_release_tag.py"),
            "--tag",
            "v{}".format(__version__),
        ],
        capture_output=True,
        text=True,
    )
    assert valid.returncode == 0
    assert json.loads(valid.stdout)["status"] == "pass"

    invalid = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_release_tag.py"), "--tag", "v9.9.9"],
        capture_output=True,
        text=True,
    )
    assert invalid.returncode != 0


def test_public_version_references_are_consistent():
    pyproject = (ROOT / "pyproject.toml").read_text()
    package_json = json.loads((ROOT / "ui/package.json").read_text())
    helper = (ROOT / "scripts/skill_workbench.py").read_text()
    assert re.search(r'^version = "{}"$'.format(re.escape(__version__)), pyproject, re.MULTILINE)
    assert package_json["version"] == __version__
    assert "@v{}".format(__version__) in helper
    for readme in ("README.md", "README.en.md", "references/visual-workbench.md"):
        assert "@v{}".format(__version__) in (ROOT / readme).read_text()
