#!/usr/bin/env python3
"""Create the separate Module 16 large-artifact ZIP without staging copies."""

from __future__ import annotations

import argparse
import os
import zipfile
from pathlib import Path


ARCHIVE_ROOT = "16_lm_head_optional_large_artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado-project", type=Path, required=True)
    parser.add_argument("--bitstream", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def require_dir(path: Path) -> Path:
    path = path.resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"required directory does not exist: {path}")
    return path


def require_file(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"required file does not exist: {path}")
    return path


def add_file(
    archive: zipfile.ZipFile,
    source: Path,
    archive_name: str,
    seen_names: set[str],
) -> int:
    archive_name = archive_name.replace("\\", "/")
    if archive_name in seen_names:
        raise ValueError(f"duplicate archive name: {archive_name}")
    seen_names.add(archive_name)
    archive.write(source, archive_name)
    return source.stat().st_size


def add_tree(
    archive: zipfile.ZipFile,
    source_root: Path,
    archive_prefix: str,
    seen_names: set[str],
    progress: dict[str, int],
) -> None:
    for source in sorted(
        (path for path in source_root.rglob("*") if path.is_file()),
        key=lambda path: path.as_posix(),
    ):
        if source.is_symlink():
            raise ValueError(f"symbolic links are not accepted: {source}")
        relative = source.relative_to(source_root).as_posix()
        size = add_file(
            archive,
            source,
            f"{ARCHIVE_ROOT}/{archive_prefix}/{relative}",
            seen_names,
        )
        progress["files"] += 1
        progress["bytes"] += size
        if progress["files"] % 500 == 0:
            print(
                "ZIP_PROGRESS "
                f"files={progress['files']} "
                f"source_bytes={progress['bytes']}",
                flush=True,
            )


def main() -> int:
    args = parse_args()
    vivado_project = require_dir(args.vivado_project)
    bitstream = require_file(args.bitstream)
    trace = require_dir(args.trace)
    readme = require_file(args.readme)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    progress = {"files": 0, "bytes": 0}
    seen_names: set[str] = set()
    with zipfile.ZipFile(
        output,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as archive:
        progress["bytes"] += add_file(
            archive,
            readme,
            f"{ARCHIVE_ROOT}/README.md",
            seen_names,
        )
        progress["files"] += 1
        add_tree(
            archive,
            vivado_project,
            "vivado_project/lm_head_axu9eg",
            seen_names,
            progress,
        )
        progress["bytes"] += add_file(
            archive,
            bitstream,
            f"{ARCHIVE_ROOT}/bitstream/lm_head_system_wrapper.bit",
            seen_names,
        )
        progress["files"] += 1
        add_tree(
            archive,
            trace,
            "trace/qwen25_0p5b_instruct_full_generation_trace",
            seen_names,
            progress,
        )

    print(
        "ZIP_CREATED "
        f"path={output} "
        f"files={progress['files']} "
        f"source_bytes={progress['bytes']} "
        f"zip_bytes={os.path.getsize(output)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
