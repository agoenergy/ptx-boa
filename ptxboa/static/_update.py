import os

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa

PYTHON_FILE = os.path.dirname(__file__) + "/__init__.py"


def sql_to_df(query: str) -> pd.DataFrame:
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek3;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    return pd.read_sql(
        query,
        engine,
    )


def update_csv(query: str, filename: str, data_dir: str | None = None) -> None:
    data_dir = data_dir or os.path.dirname(__file__)
    sql_to_df(query).to_csv(data_dir + "/" + filename, index=False, lineterminator="\n")


def create_literal(name: str, items: list) -> str:
    items_str = ", ".join(f'"{x}"' for x in items)
    return (
        f"{name}Type = Literal[{items_str}]\n"
        f"{name}Values:list[{name}Type] = [{items_str}]\n"
    )


def create_literal_from_query(name: str, column: str, query: str) -> str:
    df = sql_to_df(query)
    # choose first columns
    return create_literal(name, list(df[column]))


def create_literal_from_db(name: str, column: str, table: str) -> str:
    query = f'select "{column}" from "{table}" order by "{column}"'
    return create_literal_from_query(name, column, query)


def main():
    literals = [
        '"""DO NOT EDIT (created by static/_update.py)."""',
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
        create_literal_from_db("Chain", "chain", "ptxboa_chains"),
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
            "SecProcHEAT",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='HEAT' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "SecProcEL",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='EL' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "SecProcCCS",
            "process_name",
            (
                "SELECT process_name from ptxboa_process where "
                "main_flow_code_out='CO2-C' and is_secondary=1"
            ),
        ),
        create_literal_from_query(
            "ResGen",
            "process_name",
            "SELECT process_name from ptxboa_process where is_re_generation=1",
        ),
        create_literal_from_query(
            "ProcessCodeRes",
            "process_code",
            "SELECT process_code from ptxboa_process where is_re_generation=1",
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
                "secproc_heat",  # subset of process
                "secproc_el",  # subset of process
                "secproc_ccs",  # subset of process
                "secproc_ccs_i",  # subset of process
                "res_gen",  # subset of process
                "parameter",
            ],
        ),
        create_literal(
            "ProcessStep",
            [
                "EL_STR",  # storage electricity
                "ELY",
                "H2_STR",  # storage H2
                "DERIV",
                "DERIV2",
                "PRE_SHP",
                "SHP",
                "SHP_OWN",
                "POST_SHP",
                "PRE_PPL",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
                "POST_PPL",
                "ELY_I",
                "DERIV_I",
                "DERIV_I2",
            ],
        ),
        create_literal("ResultCost", ["CAPEX", "OPEX", "FLOW", "LC"]),
        create_literal("Transport", ["Ship", "Pipeline", "NONE"]),
        create_literal("OutputUnit", ["USD/MWh", "USD/t"]),
        create_literal("OutputUnitEmissions", ["gCO2e/MJ", "tCO2e/t", "NA"]),
        create_literal("ToolVersionColor", ["blue", "green"]),
        create_literal("ResultEmission", ["direct", "indirect"]),
        create_literal("Emission", ["mass", "emission"]),
        create_literal("ResultGas", ["CO2", "CH4"]),
        create_literal("CalculateCost", ["YES", "NO", "NG_LANDING"]),
        create_literal(
            "DataQueryParameter",
            [
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
                "default",
                "use_user_data",
                "region",
                "process_res",
                "process_ely",
                "process_deriv",
                "process_flh",
            ],
        ),
    ]

    with open(PYTHON_FILE, "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")

    update_csv(
        """
        SELECT
        "parameter_code",
        "parameter_name",
        "unit",
        "per_flow",
        "per_transformation_process",
        "per_transport_process",
        "per_re_generation_process",
        "per_process",
        "per_region",
        "per_import_country",
        "has_global_default",
        "global_default_changeable",
        "own_country_changeable",
        "comment",
        "dimensions"
        FROM "ptxboa_parameter"
        ORDER BY "parameter_code"
        """,
        "dim_parameter.csv",
    )

    update_csv(
        """
        SELECT
         "process_code"
        ,"process_name"
        ,"main_flow_code_out"
        ,"main_flow_code_in"
        ,"is_transformation"
        ,"is_re_generation"
        ,"is_transport"
        ,"is_secondary"
        ,"is_storage"
        ,"is_pipeline"
        ,"is_pipeline_retrofitted"
        ,"is_pipeline_sea"
        ,"is_shipping"
        ,"is_shipping_own_fuel"
        ,"process_class"
        ,"is_ely"
        ,"is_deriv"
        ,"result_process_type"
        ,"secondary_flows"
        ,"is_green"
        ,"is_blue"
        FROM "ptxboa_process"
        ORDER BY "process_code"
        """,
        "dim_process.csv",
    )

    update_csv(
        """
        SELECT
        "flow_code",
        "flow_name",
        "unit",
        "secondary_process",
        "secondary_flow",
        "result_process_type",
        "unit_short"
        FROM "ptxboa_flow"
        ORDER BY "flow_code"
        """,
        "dim_flow.csv",
    )

    update_csv(
        """
        SELECT
        "country_code",
        "country_name",
        "is_green",
        "is_blue"
        FROM "ptxboa_target_country"
        ORDER BY "country_code"
        """,
        "dim_country.csv",
    )

    update_csv(
        """
        SELECT
        "region_code",
        "region_name",
        "country_code",
        "subregion_code",
        "subregion_name",
        "is_coastal",
        "iso3166_code",
        "is_green",
        "is_blue"
        FROM "ptxboa_source_region"
        ORDER BY "region_code"
        """,
        "dim_region.csv",
    )

    update_csv(
        """
        SELECT
        "chain"
        ,"chain_name"
        ,"NG_PROD"
        ,"EL_STR"
        ,"ELY"
        ,"H2_STR"
        ,"DERIV"
        ,"DERIV2"
        ,"CO2_TS"
        ,"PRE_SHP"
        ,"SHP"
        ,"SHP_OWN"
        ,"POST_SHP"
        ,"PRE_PPL"
        ,"PPLS"
        ,"PPL"
        ,"PPLX"
        ,"PPLR"
        ,"POST_PPL"
        ,"ELY_I"
        ,"DERIV_I"
        ,"DERIV_I2"
        ,"CO2_TS_I"
        ,"flow_out"
        ,"can_pipeline"
        ,"is_green"
        ,"is_blue"
        FROM "ptxboa_chains"
        ORDER BY "chain"
        """,
        "chains.csv",
    )


if __name__ == "__main__":
    main()
