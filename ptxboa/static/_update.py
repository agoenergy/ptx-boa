# -*- coding: utf-8 -*-

import os

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa

PYTHON_FILE = os.path.dirname(__file__) + "/__init__.py"


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
    return f"{name}Type = Literal[{items}]\n" f"{name}Values = [{items}]\n"


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
        create_literal_from_db("Year", "year", "ptxboa_year"),
        create_literal_from_query(
            "ParameterRange",
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
        create_literal_from_db(
            "SourceRegionName", "region_name", "ptxboa_source_region"
        ),
        create_literal_from_db(
            "TargetCountryName", "country_name", "ptxboa_target_country"
        ),
        create_literal_from_db("ProcessCode", "process_code", "ptxboa_process"),
        create_literal_from_db("FlowCode", "flow_code", "ptxboa_flow"),
        create_literal_from_db("ParameterCode", "parameter_code", "ptxboa_parameter"),
        create_literal_from_db("ParameterName", "parameter_name", "ptxboa_parameter"),
        create_literal_from_db("ChainName", "chain", "ptxboa_chains"),
        create_literal_from_query(
            "Scenario",
            "scenario",
            (
                "select year + ' (' + lower(parameter_range) + ')' as scenario "
                "from ptxboa_parameter_range cross join ptxboa_year"
            ),
        ),
        create_literal_from_query(
            "ResultClass",
            "result_process_type",
            "SELECT distinct result_process_type FROM ptxboa_process_class",
        ),
        create_literal_from_query(
            "SecProcCO2",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='CO2-G' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "SecProcH2O",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='H2O-L' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "ResGen",
            "process_name",
            "SELECT process_name from ptxboa_process where is_re_generation=1",
        ),
        create_literal(
            "Dimension",
            [
                "scenario",
                "chain",
                "region",
                "country",
                "transport",
                "output_unit",
                "flow",
                "process",
                "secproc_co2",  # subset of process
                "secproc_water",  # subset of process
                "res_gen",  # subset of process
            ],
        ),
        create_literal(
            "ProcessStep",
            [
                "ELY",
                "DERIV",
                "PRE_SHP",
                "PRE_PPL",
                "POST_SHP",
                "POST_PPL",
                "SHP",
                "SHP-OWN",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
            ],
        ),
        create_literal("ResultCost", ["CAPEX", "OPEX", "FLOW", "LC"]),
        create_literal("Transport", ["Ship", "Pipeline"]),
        create_literal("OutputUnit", ["USD/MWh", "USD/t"]),
    ]

    with open(PYTHON_FILE, "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
