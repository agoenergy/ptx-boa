"""Generates classes from database data."""

import os
import re
from typing import Callable

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa

from ptxboa.classes.base import PtxboaSteps

PYTHON_FILE = os.path.dirname(__file__) + "/_generated.py"


chain_process_steps = [s.code for s in PtxboaSteps.get_all()]


def sql_to_df(query: str) -> pd.DataFrame:
    CS = (
        "mssql+pyodbc://?odbc_connect=driver=sql server;server=sqldaek3;database=ptxboa"
    )
    engine = sa.create_engine(CS)
    return pd.read_sql(
        query,
        engine,
    )


def code_to_identifier(x: str) -> str:
    x = x.upper()
    x = re.sub("[^A-Z0-9]+", "_", x)
    return x


class NoQuote:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def quote(x) -> str:
    if isinstance(x, str):
        return f"'{x}'"
    elif isinstance(x, tuple):
        return "(" + "".join(quote(y) + ", " for y in x) + ")"
    elif isinstance(x, dict):
        return "{" + ", ".join(quote(k) + ":" + quote(v) for k, v in x.items()) + "}"
    elif isinstance(x, set):
        return "{" + ", ".join(quote(k) for k in x) + "}"
    else:
        return str(x)


def get_class_instances(
    class_name: str,
    query: str,
    modify_attributes: Callable | None = None,
) -> str:
    class_name_group = f"{class_name}s"
    df = sql_to_df(query)
    lines = [
        f"class {class_name_group}(PtxboaEnum):",
    ]
    for item in df.to_dict(orient="records"):
        ident = code_to_identifier(item["code"])
        class_name_item = item.pop("class_name", class_name)
        if modify_attributes:
            item = modify_attributes(item)
        kwargs_str = ", ".join(
            f"{k}={quote(v)}"  # type:ignore
            for k, v in item.items()
        )
        line = f"    {ident} = {class_name_item}({kwargs_str})"
        lines.append(line)

    return "\n".join(lines)


def get_flow_type(flow_code: str) -> NoQuote:
    if not flow_code:
        return NoQuote("PtxboaFlowNullType")
    return NoQuote(f"PtxboaFlowTypes.{code_to_identifier(flow_code)}")


def get_process_type(process_code: str) -> NoQuote:
    if not process_code:
        return NoQuote("PtxboaProcessNullType")
    return NoQuote(f"PtxboaProcessTypes.{code_to_identifier(process_code)}")


def get_step(step_code: str) -> NoQuote:
    return NoQuote(f"PtxboaSteps.{code_to_identifier(step_code)}")


def get_sec_flow_types(x: str) -> set[NoQuote]:
    if not x:
        return set()
    return {get_flow_type(y) for y in x.split("/")}


def get_chain_steps(xs: dict) -> dict[NoQuote, NoQuote]:
    result = {}
    for s in chain_process_steps:
        process_code = xs[s]
        if not process_code:
            continue
        result[get_step(s)] = get_process_type(process_code)
    return result


def main():
    literals = [
        '"""DO NOT EDIT (created by classes/_update.py)."""',
        "from ptxboa.classes.base import PtxboaEnum, PtxboaFlowNullType, PtxboaSteps, PtxboaParameterType, PtxboaRegion, PtxboaFlowType, PtxboaChainTemplate, PtxboaChainBlueTemplate, PtxboaChainGreenTemplate",  # noqa
        "from ptxboa.classes.extra import PtxboaProcessType, PtxboaSecondaryProcessType",  # noqa
    ]

    literals.append(
        get_class_instances(
            "PtxboaParameterType",
            """SELECT
            parameter_code AS code,
            parameter_name AS name,
            'PtxboaParameterType' AS class_name /* modify in DB if needed */
            FROM ptxboa_parameter ORDER BY parameter_code""",
        )
    )

    literals.append(
        get_class_instances(
            "PtxboaFlowType",
            """SELECT
            flow_code AS code,
            flow_name AS name,
            'PtxboaFlowType' AS class_name /* modify in DB if needed */
            FROM ptxboa_flow ORDER BY flow_code""",
        )
    )

    literals.append(
        get_class_instances(
            "PtxboaRegion",
            """SELECT
            region_code AS code,
            region_name AS name,
            'PtxboaRegion' AS class_name /* modify in DB if needed */
            FROM ptxboa_source_region ORDER BY region_code""",
        )
    )

    literals.append(
        get_class_instances(
            "PtxboaProcessType",
            """SELECT
            process_code AS code,
            process_name AS name,
            main_flow_code_out as main_flow_type_out,
            main_flow_code_in as main_flow_type_in,
            secondary_flows as secondary_flow_types,
            case
              when is_secondary=1 then 'PtxboaSecondaryProcessType'
              else 'PtxboaProcessType' end AS class_name /* modify in DB if needed */
            FROM ptxboa_process ORDER BY process_code""",
            modify_attributes=lambda xs: (
                # if no secondary_flow_types: dont add
                {k: v for k, v in xs.items() if k != "secondary_flow_types"}
                | (
                    {
                        "secondary_flow_types": get_sec_flow_types(
                            xs["secondary_flow_types"]
                        ),
                    }
                    if xs["secondary_flow_types"]
                    else {}
                )
                | {
                    "main_flow_type_out": get_flow_type(xs["main_flow_type_out"]),
                    "main_flow_type_in": get_flow_type(xs["main_flow_type_in"]),
                }
            ),
        )
    )

    literals.append(
        get_class_instances(
            "PtxboaChainTemplate",
            """SELECT
            "chain" as code,
            "chain_name" as name,
            /* "NG_PROD", # sec process always in blue, if needed */
            "EL_STR",
            "ELY",
            "H2_STR",
            "DERIV",
            "DERIV2",
            /* "CO2_TS", # sec process always in blue, if needed */
            "PRE_SHP",
            "PRE_PPL",
            "POST_SHP",
            "POST_PPL",
            "SHP",
            "SHP_OWN",
            "PPLS",
            "PPL",
            "PPLX",
            "PPLR",
            "ELY_I",
            "DERIV_I",
            "DERIV_I2",
            /* "CO2_TS_I", # sec process always in blue, if needed */
            "flow_out" as flow_type_out,
            case
              when is_green=1 then 'PtxboaChainGreenTemplate'
              when is_blue=1 then 'PtxboaChainBlueTemplate'
              else 'PtxboaChainTemplate' end AS class_name /* modify in DB if needed */
            FROM ptxboa_chains ORDER BY is_green, is_blue, chain""",
            modify_attributes=lambda xs: (
                {k: xs[k] for k in ["code", "name"]}
                | {
                    "flow_type_out": get_flow_type(xs["flow_type_out"]),
                    "steps": get_chain_steps(xs),
                }
            ),
        )
    )

    with open(PYTHON_FILE, "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
