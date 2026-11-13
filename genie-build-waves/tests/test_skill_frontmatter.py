"""Every SKILL.md must have YAML frontmatter that UC Skills can parse.

The setup job publishes these files as UC Skills; publishing rejects invalid frontmatter
(for example an unquoted description containing ": "), and the skill is then not published.
"""

import pathlib

import pytest
import yaml

SKILLS = sorted((pathlib.Path(__file__).resolve().parents[1] / "src" / "skills").glob("*/SKILL.md"))


def frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "SKILL.md must start with a --- frontmatter block"
    block = text.split("---\n", 2)[1]
    data = yaml.safe_load(block)
    assert isinstance(data, dict), "frontmatter must be a YAML mapping"
    return data


def test_skills_found():
    assert len(SKILLS) >= 4


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_frontmatter_is_valid_yaml(path):
    data = frontmatter(path.read_text())
    assert data.get("name") == path.parent.name
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_unquoted_colon_is_rejected():
    with pytest.raises(yaml.YAMLError):
        frontmatter("---\nname: x\ndescription: does a (level 4: thing)\n---\n")
