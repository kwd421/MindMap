from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tarfile
import zipfile

import pytest

from mindmap.distribution_contract import (
    DistributionContractError,
    verify_distributions,
    write_sha256_manifest,
)


METADATA = """Metadata-Version: 2.4
Name: mindmap-ncm
Version: 0.2.0
License-Expression: MIT
License-File: LICENSE
Requires-Python: >=3.11
"""


def _write_wheel(path: Path, metadata: str = METADATA, *, include_license: bool = True) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mindmap_ncm-0.2.0.dist-info/METADATA", metadata)
        if include_license:
            archive.writestr(
                "mindmap_ncm-0.2.0.dist-info/licenses/LICENSE",
                "MIT License\nPermission is hereby granted, free of charge\n",
            )


def _tar_member(name: str, data: bytes) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    return info


def _write_sdist(path: Path, metadata: str = METADATA, *, include_license: bool = True) -> None:
    with tarfile.open(path, "w:gz") as archive:
        pkg = metadata.encode("utf-8")
        archive.addfile(_tar_member("mindmap_ncm-0.2.0/PKG-INFO", pkg), BytesIO(pkg))
        if include_license:
            license_data = b"MIT License\nPermission is hereby granted, free of charge\n"
            archive.addfile(
                _tar_member("mindmap_ncm-0.2.0/LICENSE", license_data),
                BytesIO(license_data),
            )


def _fixture_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    _write_wheel(dist / "mindmap_ncm-0.2.0-py3-none-any.whl")
    _write_sdist(dist / "mindmap_ncm-0.2.0.tar.gz")
    return dist


def test_valid_distribution_pair_and_sha256_manifest(tmp_path: Path) -> None:
    dist = _fixture_dist(tmp_path)
    report = verify_distributions(dist)
    assert report.license_expression == "MIT"
    assert report.license_file == "LICENSE"
    assert report.requires_python == ">=3.11"
    assert len(report.wheel_sha256) == 64
    assert len(report.sdist_sha256) == 64

    manifest = dist / "SHA256SUMS"
    write_sha256_manifest(report, manifest)
    text = manifest.read_text(encoding="utf-8")
    assert report.wheel_sha256 in text
    assert report.sdist_sha256 in text


def test_legacy_or_wrong_license_metadata_fails_closed(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    bad_metadata = METADATA.replace("License-Expression: MIT", "License: MIT")
    _write_wheel(dist / "mindmap_ncm-0.2.0-py3-none-any.whl", bad_metadata)
    _write_sdist(dist / "mindmap_ncm-0.2.0.tar.gz", bad_metadata)
    with pytest.raises(DistributionContractError, match="License-Expression"):
        verify_distributions(dist)


def test_missing_distribution_license_file_fails_closed(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _write_wheel(dist / "mindmap_ncm-0.2.0-py3-none-any.whl", include_license=False)
    _write_sdist(dist / "mindmap_ncm-0.2.0.tar.gz")
    with pytest.raises(DistributionContractError, match="licenses/LICENSE"):
        verify_distributions(dist)


def test_requires_python_mismatch_fails_closed(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    bad_metadata = METADATA.replace("Requires-Python: >=3.11", "Requires-Python: >=3.12")
    _write_wheel(dist / "mindmap_ncm-0.2.0-py3-none-any.whl", bad_metadata)
    _write_sdist(dist / "mindmap_ncm-0.2.0.tar.gz", bad_metadata)
    with pytest.raises(DistributionContractError, match="Requires-Python"):
        verify_distributions(dist)
