#!/usr/bin/env python3
"""Verify the integrity of the files committed in this edition's PR copy."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMS_FILE = ROOT / "SHA256SUMS"
MANIFEST_FILE = ROOT / "edition_manifest.json"
EXPECTED_SUM_COUNT = 14
EXPECTED_ORIGINAL_COUNT = 8
EXPECTED_PREVIEW_COUNT = 3
CORE_BINARY_FILES = {
    "rigveda-book.pdf",
    "rigveda-book.docx",
    "illustration-bundle.zip",
    "illustrations/01-cover-art.png",
    "illustrations/02-dawn.png",
    "illustrations/03-cosmos-and-voice.png",
}
EXPECTED_ZIP_MEMBERS = {
    "illustrations/01-cover-art.png",
    "illustrations/02-dawn.png",
    "illustrations/03-cosmos-and-voice.png",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize_path(raw: str) -> str:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        fail(f"unsafe relative path: {raw!r}")
    normalized = candidate.as_posix()
    if normalized in ("", "."):
        fail(f"empty file path: {raw!r}")
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"path escapes edition directory: {raw!r}")
    return normalized


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_sums() -> dict[str, str]:
    if not SUMS_FILE.is_file():
        fail("SHA256SUMS is missing")
    records: dict[str, str] = {}
    pattern = re.compile(r"^([0-9a-fA-F]{64})[ \t]+[*]?(.+)$")
    for line_number, line in enumerate(SUMS_FILE.read_text(encoding="utf-8").splitlines(), 1):
        match = pattern.fullmatch(line)
        if not match:
            fail(f"malformed SHA256SUMS line {line_number}")
        expected, raw_path = match.groups()
        rel = normalize_path(raw_path)
        if rel in records:
            fail(f"duplicate SHA256SUMS path: {rel}")
        records[rel] = expected.lower()
    if len(records) != EXPECTED_SUM_COUNT:
        fail(f"expected {EXPECTED_SUM_COUNT} SHA256SUMS entries, found {len(records)}")
    return records


def main() -> None:
    sums = read_sums()
    actual_hashes: dict[str, str] = {}

    for rel, expected in sums.items():
        path = ROOT / rel
        if not path.is_file():
            fail(f"SHA256SUMS file is missing: {rel}")
        actual = sha256_file(path)
        if actual != expected:
            fail(f"SHA-256 mismatch: {rel}")
        actual_hashes[rel] = actual
        print(f"OK SHA-256  {rel}")

    if not MANIFEST_FILE.is_file():
        fail("edition_manifest.json is missing")
    try:
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot parse edition_manifest.json: {exc}")

    originals = manifest.get("original_files")
    previews = manifest.get("notion_previews")
    if not isinstance(originals, list) or len(originals) != EXPECTED_ORIGINAL_COUNT:
        fail(f"expected {EXPECTED_ORIGINAL_COUNT} original_files in manifest")
    if not isinstance(previews, list) or len(previews) != EXPECTED_PREVIEW_COUNT:
        fail(f"expected {EXPECTED_PREVIEW_COUNT} notion_previews in manifest")

    manifest_entries = originals + previews
    manifest_paths: set[str] = set()
    for entry in manifest_entries:
        if not isinstance(entry, dict):
            fail("manifest file entry is not an object")
        rel = normalize_path(str(entry.get("path", "")))
        if rel in manifest_paths:
            fail(f"duplicate manifest path: {rel}")
        manifest_paths.add(rel)
        if rel not in sums:
            fail(f"manifest file is not covered by SHA256SUMS: {rel}")
        path = ROOT / rel
        if not path.is_file():
            fail(f"manifest file is missing: {rel}")
        size = entry.get("size_bytes")
        if not isinstance(size, int) or path.stat().st_size != size:
            fail(f"size mismatch for manifest file: {rel}")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or actual_hashes[rel] != digest.lower():
            fail(f"manifest SHA-256 mismatch: {rel}")

    missing_core = CORE_BINARY_FILES - sums.keys()
    if missing_core:
        fail("core binary files not covered by SHA256SUMS: " + ", ".join(sorted(missing_core)))

    zip_path = ROOT / "illustration-bundle.zip"
    try:
        with zipfile.ZipFile(zip_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                fail(f"ZIP CRC failure: {bad_member}")
            members = set(archive.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        fail(f"cannot test illustration-bundle.zip: {exc}")
    missing_members = EXPECTED_ZIP_MEMBERS - members
    if missing_members:
        fail("ZIP is missing original PNGs: " + ", ".join(sorted(missing_members)))

    print(f"PASS: {len(sums)} SHA256SUMS entries verified")
    print(f"PASS: {len(manifest_entries)} manifest files match their declared sizes and SHA-256 values")
    print(f"PASS: all {len(CORE_BINARY_FILES)} core binary files are covered by SHA256SUMS")
    print(f"PASS: illustration-bundle.zip CRC test passed; {len(members)} members, all three original PNGs present")
    print("NOTE: all hashes above verify this checked-out PR copy, not an independent comparison with source originals.")


if __name__ == "__main__":
    main()
