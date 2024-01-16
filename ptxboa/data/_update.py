# -*- coding: utf-8 -*-
"""Update csv files from Database."""

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa


def update_csv(table, fields, filename, where=""):
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek2;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    fields = ",".join(f'"{f}"' for f in fields)
    pd.read_sql(
        f'select {fields} from "{table}" {where} order by "key"',
        engine,
    ).to_csv(filename, index=False)


if __name__ == "__main__":
    update_csv(
        "ptxboa_data_flh_view",
        [
            "key",
            "region",
            "process_res",
            "process_ely",
            "process_deriv",
            "process_flh",
            "value",
            "source",
        ],
        "flh.csv",
        where="where value is not null",
    )
    update_csv(
        "ptxboa_data_storage_factor",
        [
            "key",
            "process_res",
            "process_ely",
            "process_deriv",
            "value",
            "source",
        ],
        "storage_cost_factor.csv",
        where="where value is not null",
    )

    for year in [2030, 2040]:
        for rng in ["high", "medium", "low"]:
            update_csv(
                "ptxboa_data_latest_full",
                [
                    "key",
                    "parameter_code",
                    "process_code",
                    "flow_code",
                    "source_region_code",
                    "target_country_code",
                    "value",
                    "unit",
                    "source",
                ],
                f"{year}_{rng}.csv",
                where=f"""where
                "year"={year} and
                "parameter_range"='{rng}' and
                value is not null
                """,
            )
