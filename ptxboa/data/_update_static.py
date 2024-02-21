# -*- coding: utf-8 -*-

import os

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa


def sql_to_df(query: str) -> pd.DataFrame:
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek2;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    return pd.read_sql(
        query,
        engine,
    )


def create_literal(name: str, items: list) -> str:
    items = ", ".join(f'"{x}"' for x in items)
    return f"{name} = Literal[{items}]"


def create_literal_from_query(name: str, column: str, query: str) -> str:
    df = sql_to_df(query)
    # choose first columns
    return create_literal(name, list(df[column]))


def create_literal_from_db(name: str, column: str, table: str) -> str:
    query = f'select "{column}" from "{table}" order by "{column}"'
    return create_literal_from_query(name, column, query)


def main():

    literals = [
        '"""DO NOT EDIT (created by _update_static.py)."""',
        "from typing import Literal",
        create_literal_from_db("YearCode", "year", "ptxboa_year"),
        create_literal_from_query(
            "ParameterRangeCode",
            "parameter_range",
            (
                "select lower(parameter_range) as parameter_range "
                "from ptxboa_parameter_range"
            ),
        ),
        create_literal_from_db(
            "SourceRegionCode", "region_code", "ptxboa_source_region"
        ),
        create_literal_from_db(
            "TargetCountryCode", "country_code", "ptxboa_target_country"
        ),
        create_literal_from_db("ProcessCode", "process_code", "ptxboa_process"),
        create_literal_from_db("FlowCode", "flow_code", "ptxboa_flow"),
        create_literal_from_db("ParameterCode", "parameter_code", "ptxboa_parameter"),
        create_literal_from_query(
            "ScenarioCode",
            "scenario",
            (
                "select year + ' (' + lower(parameter_range) + ')' as scenario "
                "from ptxboa_parameter_range cross join ptxboa_year"
            ),
        ),
        create_literal_from_query(
            "ResultProcessTypes",
            "result_process_type",
            "SELECT distinct result_process_type FROM ptxboa_process_class",
        ),
    ]

    with open(os.path.dirname(__file__) + "/static.py", "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
