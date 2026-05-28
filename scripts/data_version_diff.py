"""Data difference for input csv files."""

import argparse
import subprocess  # noqa S404
from io import StringIO

import pandas as pd

ALLOWED_PATHS = [
    "ptxboa/data/2030_high.csv",
    "ptxboa/data/2030_low.csv",
    "ptxboa/data/2030_medium.csv",
    "ptxboa/data/2040_high.csv",
    "ptxboa/data/2040_low.csv",
    "ptxboa/data/2040_medium.csv",
]


def load_csv_from_git(commit_hash: str, filepath: str) -> pd.DataFrame:
    result = subprocess.run(  # noqa S607
        ["git", "show", f"{commit_hash}:{filepath}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return pd.read_csv(StringIO(result.stdout))


def compare_csv(commit_hash: str, filepath: str, commit_hash_compare: str | None):
    if commit_hash_compare is None:
        commit_hash_compare = f"{commit_hash}^1"

    before = load_csv_from_git(commit_hash_compare, filepath)
    after = load_csv_from_git(commit_hash, filepath)

    before = before.set_index("key")
    after = after.set_index("key")

    combined = before.join(after, lsuffix="_before", rsuffix="_after", how="outer")
    combined = combined[sorted(combined.columns)]

    # Detect changes
    combined["status"] = "unchanged_value"
    combined.loc[combined.index.difference(before.index), "status"] = "added_value"
    combined.loc[combined.index.difference(after.index), "status"] = "removed_value"

    combined["value_diff"] = combined["value_after"] - combined["value_before"]
    combined["value_rel_diff"] = combined["value_diff"] / combined["value_before"]

    # Avoid division by zero
    combined.loc[combined["value_before"] == 0, "value_rel_diff"] = None
    combined.loc[
        (combined["value_diff"] != 0) & (combined["status"] == "unchanged_value"),
        "status",
    ] = "changed_value"

    output_file = f"compare_{filepath.split('/')[-1]}_{commit_hash}.xlsx"
    combined.to_excel(output_file)

    print(f"Comparison written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare CSV file versions between git commits"
    )

    parser.add_argument(
        "commit",
        help="Target commit hash",
    )

    parser.add_argument(
        "filepath",
        choices=ALLOWED_PATHS,
        help="CSV file path (restricted set)",
    )

    parser.add_argument(
        "--compare",
        dest="commit_compare",
        help="Optional commit to compare against (default: parent commit)",
        default=None,
    )

    args = parser.parse_args()

    compare_csv(
        commit_hash=args.commit,
        filepath=args.filepath,
        commit_hash_compare=args.commit_compare,
    )


if __name__ == "__main__":
    main()
