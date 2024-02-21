# -*- coding: utf-8 -*-
"""Update csv files from Database."""

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa


def update_csv(query, filename):
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek2;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    pd.read_sql(
        query,
        engine,
    ).to_csv(filename, index=False, lineterminator="\n")


def main():
    update_csv(
        """
        SELECT
        "chain"
        ,"ELY"
        ,"DERIV"
        ,"PRE_SHP"
        ,"PRE_PPL"
        ,"POST_SHP"
        ,"POST_PPL"
        ,"SHP"
        ,"SHP-OWN"
        ,"PPLS"
        ,"PPL"
        ,"PPLX"
        ,"PPLR"
        ,"FLOW_OUT"
        ,"CAN_PIPELINE"
        FROM "ptxboa_chains"
        ORDER BY "chain"
        """,
        "chains.csv",
    )

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
        "comment"
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
        /*,"process_class"*/
        ,"is_secondary_all"
        ,"is_ely"
        ,"is_deriv"
        /*,"class_name"*/
        ,"result_process_type"
        ,"secondary_flows"
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
        "result_process_type"
        FROM "ptxboa_flow"
        ORDER BY "flow_code"
        """,
        "dim_flow.csv",
    )

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
