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
    try:
        result = subprocess.run(  # noqa S607
            ["git", "show", f"{commit_hash}:{filepath}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to load '{filepath}' at commit '{commit_hash}'"
        ) from e

    return pd.read_csv(StringIO(result.stdout))


def get_parent(commit: str) -> str:
    try:
        result = subprocess.run(  # noqa S607
            ["git", "rev-parse", f"{commit}^1"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(f"Commit '{commit}' has no parent")


def compare_csv(
    commit_hash: str,
    filepath: str,
    commit_hash_compare: str | None,
):
    if commit_hash_compare is None:
        commit_hash_compare = get_parent(commit_hash)

    before = load_csv_from_git(commit_hash_compare, filepath)
    after = load_csv_from_git(commit_hash, filepath)

    if "value" not in before.columns or "value" not in after.columns:
        raise ValueError("CSV must contain a 'value' column")

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

    # Detect changed rows
    mask_changed = (
        (combined["status"] == "unchanged_value")
        & combined["value_before"].notna()
        & combined["value_after"].notna()
        & (combined["value_diff"] != 0)
    )
    combined.loc[mask_changed, "status"] = "changed_value"

    short_commit = commit_hash[:7]
    short_compare = commit_hash_compare[:7]
    filename = filepath.split("/")[-1].replace(".csv", "")

    output_file = f"compare_{filename}_{short_compare}_to_{short_commit}.xlsx"
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
