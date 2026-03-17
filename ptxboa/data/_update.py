"""Update csv files from Database."""

import os

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa


def update_csv(
    query: str,
    filename: str,
    data_dir: str | None = None,
    check_uniue_cols: list | None = None,
) -> None:
    data_dir = data_dir or os.path.dirname(__file__)
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek3;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    df = pd.read_sql(
        query,
        engine,
    )
    if check_uniue_cols:
        idx_duplicated = df.fillna("").duplicated(check_uniue_cols, keep=False)
        if idx_duplicated.any():
            raise Exception(
                (filename, df.loc[idx_duplicated].sort_values(check_uniue_cols))
            )

    df.to_csv(data_dir + "/" + filename, index=False, lineterminator="\n")


def main():

    update_csv(
        """
        SELECT
        "key",
        "region",
        "process_res",
        "process_ely",
        "process_deriv",
        "process_flh",
        "value",
        "source"
        FROM "ptxboa_data_flh_view"
        WHERE "value" is not null
        ORDER BY "key"
        """,
        "flh.csv",
    )

    for year in [2030, 2040]:
        for rng in ["high", "medium", "low"]:
            update_csv(
                f"""
                select
                "key",
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
                "value",
                "unit",
                "source"
                FROM "ptxboa_data_latest_full"
                where
                "year"={year} and
                "parameter_range"='{rng}' and
                "value" is not null
                order by "key"
                """,
                f"{year}_{rng}.csv",
                check_uniue_cols=[
                    "parameter_code",
                    "process_code",
                    "flow_code",
                    "source_region_code",
                    "target_country_code",
                ],
            )


if __name__ == "__main__":
    main()
