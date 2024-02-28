# -*- coding: utf-8 -*-
"""Update csv files from Database."""

import os

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa


def update_csv(query: str, filename: str, data_dir: str = None) -> None:
    data_dir = data_dir or os.path.dirname(__file__)
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek2;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    pd.read_sql(
        query,
        engine,
    ).to_csv(data_dir + "/" + filename, index=False, lineterminator="\n")


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
    update_csv(
        """
        select
        "key",
        "process_res",
        "process_ely",
        "process_deriv",
        "value",
        "source"
        FROM "ptxboa_data_storage_factor"
        WHERE value is not null
        ORDER BY "key"
        """,
        "storage_cost_factor.csv",
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
            )


if __name__ == "__main__":
    main()
