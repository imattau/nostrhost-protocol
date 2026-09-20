"""Kind registry tests: constants, retention classes, manifest consistency."""

from __future__ import annotations

import pytest

import nostrhost_protocol as p
from nostrhost_protocol import kinds
from nostrhost_protocol.manifest import validate_manifest


def test_module_alias_equals_int():
    assert p.KindOperationRequest == 2200
    assert p.KIND_SYSTEM_EVENT == 2210
    assert p.KIND_PERMISSION_SET == 30000
    assert p.KIND_NIP98 == 27235


def test_kind_members_unique():
    values = [member.value for member in p.Kind]
    assert len(values) == len(set(values))


def test_manifest_has_no_duplicates_or_broken_refs():
    problems = validate_manifest()
    assert problems == [], problems


def test_manifest_matches_kind_enum():
    manifest_kinds = {spec.kind for spec in p.load_manifest()}
    enum_kinds = {int(member) for member in p.Kind}
    assert manifest_kinds == enum_kinds, (
        manifest_kinds ^ enum_kinds
    )


def test_manifest_rejection_codes_cover_corpus_codes():
    corpus_codes = set()
    for fixture in p.load_verdicts():
        expect = fixture["expect"]
        if not expect["accept"]:
            corpus_codes.add(expect["code"])
    manifest_codes = set(p.__dict__ and p.load_manifest().__class__ and _manifest_codes())
    # Every code that appears in the corpus must be declared in the manifest.
    assert corpus_codes <= manifest_codes, corpus_codes - manifest_codes


def _manifest_codes() -> set[str]:
    result: set[str] = set()
    for spec in p.load_manifest():
        result.update(spec.rejection_codes)
    return result


def test_retention_class():
    assert p.retention_class(2200) == "immutable"
    assert p.retention_class(2210) == "immutable"
    assert p.retention_class(27236) == "immutable"
    assert p.retention_class(31100) == "replaceable"
    assert p.retention_class(30000) == "replaceable"
    assert p.retention_class(22242) == "ephemeral"


def test_is_custom_kind():
    assert p.is_custom_kind(2200)
    assert p.is_custom_kind(31100)
    assert not p.is_custom_kind(1)
    assert not p.is_custom_kind(32267)


def test_chain_kinds_order():
    assert p.chain_kinds() == [2200, 2201, 2202, 2203, 2204]
    assert list(p.CHAIN_KINDS) == [2200, 2201, 2202, 2203, 2204]


def test_json_content_and_addressable_sets():
    assert p.JSON_CONTENT_KINDS == {31100, 31101, 31102}
    assert p.ADDRESSABLE_KINDS == {31100, 31101, 31102, 30000, 30078}
    assert p.HEX64_D_KINDS == {31100, 31102}


@pytest.mark.parametrize("name", ["KindOperationRequest", "KIND_SYSTEM_EVENT", "KindCapability"])
def test_kind_aliases_exist(name):
    assert hasattr(kinds, name)