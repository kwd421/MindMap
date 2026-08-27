from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "gatemem_external.py"


def _module():
    spec = importlib.util.spec_from_file_location("gatemem_external_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_opaque_secret_file_is_optional(tmp_path: Path):
    assert _module()._load_opaque_secret(None) is None


def test_opaque_secret_file_requires_existing_128_bit_minimum(tmp_path: Path):
    module = _module()
    with pytest.raises(ValueError, match="is missing"):
        module._load_opaque_secret(tmp_path / "missing.bin")

    too_short = tmp_path / "short.bin"
    too_short.write_bytes(b"x" * 15)
    with pytest.raises(ValueError, match="at least 128 bits"):
        module._load_opaque_secret(too_short)


def test_opaque_secret_file_returns_exact_bytes_without_serialization(
    tmp_path: Path,
):
    secret = bytes(range(32))
    path = tmp_path / "opaque.bin"
    path.write_bytes(secret)
    assert _module()._load_opaque_secret(path) == secret
