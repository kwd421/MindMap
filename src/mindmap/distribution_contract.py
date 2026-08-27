from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import tarfile
import zipfile


class DistributionContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DistributionReport:
    wheel: Path
    sdist: Path
    wheel_sha256: str
    sdist_sha256: str
    license_expression: str
    license_file: str
    requires_python: str

    def render(self) -> str:
        return "\n".join(
            (
                "MindMap distribution contract",
                f"wheel={self.wheel.name}",
                f"wheel_sha256={self.wheel_sha256}",
                f"sdist={self.sdist.name}",
                f"sdist_sha256={self.sdist_sha256}",
                f"license_expression={self.license_expression}",
                f"license_file={self.license_file}",
                f"requires_python={self.requires_python}",
                "ok=true",
            )
        )


def _digest(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _metadata_field(text: str, field: str) -> str:
    prefix = f"{field}: "
    values = [line[len(prefix):].strip() for line in text.splitlines() if line.startswith(prefix)]
    if len(values) != 1:
        raise DistributionContractError(
            f"expected exactly one {field!r} metadata field, found {len(values)}"
        )
    return values[0]


def _wheel_metadata(wheel: Path) -> tuple[str, set[str]]:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise DistributionContractError(
                f"wheel must contain exactly one .dist-info/METADATA, found {len(metadata_names)}"
            )
        metadata = archive.read(metadata_names[0]).decode("utf-8")
    return metadata, names


def _sdist_metadata(sdist: Path) -> tuple[str, set[str]]:
    with tarfile.open(sdist, mode="r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        names = {member.name for member in members}
        pkg_info = [member for member in members if member.name.count("/") == 1 and member.name.endswith("/PKG-INFO")]
        if len(pkg_info) != 1:
            raise DistributionContractError(
                f"sdist must contain exactly one top-level PKG-INFO, found {len(pkg_info)}"
            )
        extracted = archive.extractfile(pkg_info[0])
        if extracted is None:
            raise DistributionContractError("could not read sdist PKG-INFO")
        metadata = extracted.read().decode("utf-8")
    return metadata, names


def verify_distributions(
    dist_dir: Path,
    *,
    expected_license_expression: str = "MIT",
    expected_license_file: str = "LICENSE",
    expected_requires_python: str = ">=3.11",
) -> DistributionReport:
    dist_dir = dist_dir.resolve()
    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    if len(wheels) != 1:
        raise DistributionContractError(f"expected one wheel, found {len(wheels)}")
    if len(sdists) != 1:
        raise DistributionContractError(f"expected one sdist, found {len(sdists)}")

    wheel = wheels[0]
    sdist = sdists[0]
    wheel_metadata, wheel_names = _wheel_metadata(wheel)
    sdist_metadata, sdist_names = _sdist_metadata(sdist)

    wheel_license = _metadata_field(wheel_metadata, "License-Expression")
    wheel_license_file = _metadata_field(wheel_metadata, "License-File")
    wheel_python = _metadata_field(wheel_metadata, "Requires-Python")
    sdist_license = _metadata_field(sdist_metadata, "License-Expression")
    sdist_license_file = _metadata_field(sdist_metadata, "License-File")
    sdist_python = _metadata_field(sdist_metadata, "Requires-Python")

    expected = (
        ("wheel License-Expression", wheel_license, expected_license_expression),
        ("sdist License-Expression", sdist_license, expected_license_expression),
        ("wheel License-File", wheel_license_file, expected_license_file),
        ("sdist License-File", sdist_license_file, expected_license_file),
        ("wheel Requires-Python", wheel_python, expected_requires_python),
        ("sdist Requires-Python", sdist_python, expected_requires_python),
    )
    for label, observed, wanted in expected:
        if observed != wanted:
            raise DistributionContractError(f"{label}: expected {wanted!r}, got {observed!r}")

    wheel_license_paths = [
        name for name in wheel_names if name.endswith(f".dist-info/licenses/{expected_license_file}")
    ]
    if len(wheel_license_paths) != 1:
        raise DistributionContractError(
            "wheel must contain exactly one .dist-info/licenses/LICENSE file"
        )
    sdist_license_paths = [
        name for name in sdist_names if name.count("/") == 1 and name.endswith(f"/{expected_license_file}")
    ]
    if len(sdist_license_paths) != 1:
        raise DistributionContractError("sdist must contain the top-level LICENSE file")

    return DistributionReport(
        wheel=wheel,
        sdist=sdist,
        wheel_sha256=_digest(wheel),
        sdist_sha256=_digest(sdist),
        license_expression=wheel_license,
        license_file=wheel_license_file,
        requires_python=wheel_python,
    )


def write_sha256_manifest(report: DistributionReport, output: Path) -> None:
    output.write_text(
        "".join(
            (
                f"{report.sdist_sha256}  {report.sdist.name}\n",
                f"{report.wheel_sha256}  {report.wheel.name}\n",
            )
        ),
        encoding="utf-8",
    )
