#!/usr/bin/env python3

import argparse
import json
import math
import random
import shutil
from pathlib import Path


def percentage(value):
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Percentage must be a number.")

    if not 0 <= number <= 100:
        raise argparse.ArgumentTypeError("Percentage must be between 0 and 100.")

    return number


def main():
    parser = argparse.ArgumentParser(
        description="Randomly sample files from each JSON key and copy them."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="JSON file mapping keys to lists of file paths.",
    )
    parser.add_argument(
        "--percentage",
        type=percentage,
        default=20.0,
        help="Percentage to sample from each key (default: 20).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("abillation.json"),
        help="Output JSON file (default: abillation.json).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("selected_files"),
        help="Directory for copied files (default: selected_files).",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Resolve relative source paths against this directory "
             "(default: the input JSON's directory).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed for reproducible selection.",
    )
    args = parser.parse_args()

    try:
        input_json = args.input_json.resolve()
        output_json = args.output_json.resolve()
        output_dir = args.output_dir.resolve()
        base_dir = (
            args.base_dir.resolve()
            if args.base_dir is not None
            else input_json.parent
        )

        if input_json == output_json:
            raise ValueError("Output JSON must not overwrite the input JSON.")

        with input_json.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("Input JSON must be an object mapping keys to lists.")

        rng = random.Random(args.seed)
        copy_plan = []

        for group_index, (key, paths) in enumerate(data.items(), start=1):
            if not isinstance(paths, list) or not all(
                isinstance(path, str) and path for path in paths
            ):
                raise ValueError(
                    f"Value for {key!r} must be a list of nonempty path strings."
                )

            # Remove duplicate path strings while preserving order.
            unique_paths = list(dict.fromkeys(paths))

            # Calculate the target BEFORE filtering out missing files.
            target_count = math.floor(
                len(unique_paths) * args.percentage / 100
            )

            existing_files = []

            for path_string in unique_paths:
                source = Path(path_string)
                #if not source.is_absolute():
                #    source = base_dir / source
                source = source.resolve()

                if source.is_file():
                    existing_files.append(source)
                else:
                    print(f"Warning: skipping missing or non-file path: {source}")

            # Sampling without replacement requires enough existing files.
            if len(existing_files) < target_count:
                raise ValueError(
                    f"{key!r}: need {target_count} files "
                    f"({args.percentage}% of {len(unique_paths)} paths), "
                    f"but only {len(existing_files)} exist. "
                    "Cannot maintain the requested sample size."
                )

            selected_files = rng.sample(existing_files, target_count)

            print(
                f"{key}: selected {target_count} files "
                f"from {len(existing_files)} existing files "
                f"({len(unique_paths)} original paths)"
            )

            for file_index, source in enumerate(selected_files, start=1):
                destination = (
                    output_dir
                    / f"group_{group_index:04d}"
                    / f"{file_index:06d}_{source.name}"
                )

                if destination == source:
                    raise ValueError(
                        f"Cannot copy a file onto itself: {source}"
                    )

                copy_plan.append((source, destination))
        # All selected source files have been checked before copying begins.
        output_dir.mkdir(parents=True, exist_ok=True)
        copied_paths = []

        for source, destination in copy_plan:
            print(f"Copying {source} to {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied_paths.append(str(destination))

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with output_json.open("w", encoding="utf-8") as handle:
            json.dump({"abillation": copied_paths}, handle, indent=2)
            handle.write("\n")

        print(f"Copied {len(copied_paths)} files to {output_dir}")
        print(f"Wrote {output_json}")

    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
