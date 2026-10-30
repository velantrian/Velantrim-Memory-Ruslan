#!/usr/bin/env python3
"""Rebuild full-resolution PNGs from the ZIP_STORED parts attached in Notion."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("restored-illustrations"),
        help="where reconstructed PNGs are written (default: restored-illustrations)",
    )
    parser.add_argument(
        "--verify-originals",
        action="store_true",
        help="also compare each reconstruction with assets/<original filename>",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing output only after its contents have been verified",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent.parent
    chunk_dir = base / "notion-illustration-chunks"
    manifest_path = chunk_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "HARVYRD-NOTION-ILLUSTRATION-CHUNKS-v1":
        raise SystemExit(f"Unsupported manifest format: {manifest.get('format')!r}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in manifest["files"]:
        pieces = sorted(item["parts"], key=lambda part: part["index"])
        if not pieces or len(pieces) != item["part_count"]:
            raise SystemExit(f"Part-count mismatch for {item['original_filename']}")
        rebuilt = bytearray()
        expected_offset = 0

        for expected_index, part in enumerate(pieces, start=1):
            if part["index"] != expected_index or part["part_count"] != len(pieces):
                raise SystemExit(f"Part ordering/count mismatch: {part['filename']}")
            if part["offset"] != expected_offset:
                raise SystemExit(f"Non-contiguous offset in {part['filename']}")

            archive_path = chunk_dir / part["filename"]
            archive_bytes = archive_path.read_bytes()
            if sha256(archive_bytes) != part["zip_sha256"]:
                raise SystemExit(f"ZIP checksum mismatch: {archive_path.name}")
            if len(archive_bytes) != part["zip_size_bytes"]:
                raise SystemExit(f"ZIP size mismatch: {archive_path.name}")
            if len(archive_bytes) >= 4 * 1024 * 1024:
                raise SystemExit(f"ZIP is not below 4 MiB: {archive_path.name}")

            with zipfile.ZipFile(archive_path, "r") as archive:
                infos = archive.infolist()
                if len(infos) != 1 or infos[0].filename != "data.bin":
                    raise SystemExit(f"Unexpected ZIP members: {archive_path.name}")
                if infos[0].compress_type != zipfile.ZIP_STORED:
                    raise SystemExit(f"ZIP member is not ZIP_STORED: {archive_path.name}")
                payload = archive.read("data.bin")  # also checks the ZIP CRC

            if len(payload) != part["length_bytes"]:
                raise SystemExit(f"Part length mismatch: {archive_path.name}")
            if sha256(payload) != part["payload_sha256"]:
                raise SystemExit(f"Part payload checksum mismatch: {archive_path.name}")
            rebuilt.extend(payload)
            expected_offset += len(payload)

        if len(rebuilt) != item["size_bytes"]:
            raise SystemExit(f"Reconstructed size mismatch: {item['original_filename']}")
        if sha256(rebuilt) != item["original_sha256"]:
            raise SystemExit(f"Reconstructed SHA-256 mismatch: {item['original_filename']}")

        destination = args.output_dir / item["original_filename"]
        if destination.exists() and not args.force:
            if destination.read_bytes() != rebuilt:
                raise SystemExit(
                    f"Refusing to replace different file {destination}; use --force"
                )
        else:
            destination.write_bytes(rebuilt)

        if args.verify_originals:
            source = base / "assets" / item["original_filename"]
            if not source.is_file() or source.read_bytes() != rebuilt:
                raise SystemExit(f"Reconstruction differs from GitHub original: {source}")
        print(
            f"OK {item['original_filename']}: {len(rebuilt)} bytes, "
            f"SHA-256 {item['original_sha256']}"
        )
        count += 1

    print(f"Restored and verified {count} full-resolution PNG files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
