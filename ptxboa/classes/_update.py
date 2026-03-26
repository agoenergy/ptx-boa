"""Generates classes from database data."""

import os
import re
from typing import Callable

import pandas as pd
import pyodbc  # noqa
import sqlalchemy as sa

PYTHON_FILE = os.path.dirname(__file__) + "/_generated.py"


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


def get_class_definitions_instances(
    class_name: str,
    query: str,
    modify_attributes: dict[str, Callable] | None = None,
    is_instance: bool = False,
) -> str:
    modify_attributes = modify_attributes or {}
    class_name_group = f"{class_name}s"
    df = sql_to_df(query)
    lines = [
        f"class {class_name_group}:",
    ]
    for item in df.to_dict(orient="records"):
        ident = code_to_identifier(item["code"])
        clsname = f"{class_name}_{ident}"
        kwargs_str = ", ".join(
            f"{k}={modify_attributes.get(k, repr)(v)}"  # type:ignore
            for k, v in item.items()
        )
        if is_instance:
            line = f"({kwargs_str})"
        else:
            line = f'._create_subclass("{clsname}", {kwargs_str})'
        line = f"    {ident} = ptxboa.classes.base.{class_name}" + line
        lines.append(line)

    return "\n".join(lines)


def get_flow(flow_code: str) -> str:
    if not flow_code:
        return "ptxboa.classes.base.PtxboaFlowNull"
    return f"PtxboaFlows.{code_to_identifier(flow_code)}"


def main():
    cls_import = [  # noqa
        "PtxboaParameter",
        "PtxboaProcess",
        "PtxboaFlow",
        "PtxboaRegion",
        "PtxboaFlowNull",
    ]
    # cls_import_unused = ["PtxboaChain"] # noqa

    literals = [
        '"""DO NOT EDIT (created by classes/_update.py)."""',
        # "from ptxboa.classes.base import %s" % ", ".join(cls_import), # noqa
        # "from ptxboa.classes.base import %s" % ", ".join(cls_import_unused), # noqa
        # "__all__ = [%s]" % ", ".join(f'"{c}"' for c in cls_import_unused), # noqa
        "import ptxboa.classes.base",
    ]

    literals.append(
        get_class_definitions_instances(
            "PtxboaParameter",
            """SELECT
            parameter_code AS code,
            parameter_name AS name,
            'PtxboaParameter' AS template_class_name
            FROM ptxboa_parameter ORDER BY parameter_code""",
        )
    )

    literals.append(
        get_class_definitions_instances(
            "PtxboaFlow",
            """SELECT
            flow_code AS code,
            flow_name AS name,
            'PtxboaFlow' AS template_class_name
            FROM ptxboa_flow ORDER BY flow_code""",
        )
    )

    literals.append(
        get_class_definitions_instances(
            "PtxboaRegion",
            """SELECT
            region_code AS code,
            region_name AS name
            FROM ptxboa_source_region ORDER BY region_code""",
            is_instance=True,
        )
    )

    literals.append(
        get_class_definitions_instances(
            "PtxboaProcess",
            """SELECT
            process_code AS code,
            process_name AS name,
            main_flow_code_out as main_flow_type_out,
            main_flow_code_in as main_flow_type_in,
            'PtxboaProcess' AS template_class_name
            FROM ptxboa_process ORDER BY process_code""",
            modify_attributes={
                "main_flow_type_out": get_flow,
                "main_flow_type_in": get_flow,
            },
        )
    )

    with open(PYTHON_FILE, "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
