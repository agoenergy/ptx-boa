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
        create_literal_from_db("YearCodeType", "year", "ptxboa_year"),
        create_literal_from_query(
            "ParameterRangeCodeType",
            "parameter_range",
            (
                "select lower(parameter_range) as parameter_range "
                "from ptxboa_parameter_range"
            ),
        ),
        create_literal_from_db(
            "SourceRegionCodeType", "region_code", "ptxboa_source_region"
        ),
        create_literal_from_db(
            "TargetCountryCodeType", "country_code", "ptxboa_target_country"
        ),
        create_literal_from_db(
            "SourceRegionNameType", "region_name", "ptxboa_source_region"
        ),
        create_literal_from_db(
            "TargetCountryNameType", "country_name", "ptxboa_target_country"
        ),
        create_literal_from_db("ProcessCodeType", "process_code", "ptxboa_process"),
        create_literal_from_db("FlowCodeType", "flow_code", "ptxboa_flow"),
        create_literal_from_db(
            "ParameterCodeType", "parameter_code", "ptxboa_parameter"
        ),
        create_literal_from_db(
            "ParameterNameType", "parameter_name", "ptxboa_parameter"
        ),
        create_literal_from_db("ChainNameType", "chain", "ptxboa_chains"),
        create_literal_from_query(
            "ScenarioCodeType",
            "scenario",
            (
                "select year + ' (' + lower(parameter_range) + ')' as scenario "
                "from ptxboa_parameter_range cross join ptxboa_year"
            ),
        ),
        create_literal_from_query(
            "ResultProcessType",
            "result_process_type",
            "SELECT distinct result_process_type FROM ptxboa_process_class",
        ),
        create_literal_from_query(
            "SecProcCO2Type",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='CO2-G' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "SecProcH2OType",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='H2O-L' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "ResGenType",
            "process_name",
            "SELECT process_name from ptxboa_process where is_re_generation=1",
        ),
    ]

    with open(os.path.dirname(__file__) + "/static.py", "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
