#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def load_json_object(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Merge two JSON files, giving the second file priority."
    )
    parser.add_argument("first", type=Path, help="First JSON file.")
    parser.add_argument("second", type=Path, help="Second JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("merged.json"),
        help="Output file (default: merged.json).",
    )
    args = parser.parse_args()

    try:
        first = load_json_object(args.first)
        second = load_json_object(args.second)

        first.update(second)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as file:
            json.dump(first, file, indent=2, ensure_ascii=False)
            file.write("\n")

        print(f"Merged JSON saved to {args.output}")

    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()