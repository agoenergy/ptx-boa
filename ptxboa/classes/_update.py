"""Generates classes from database data."""

import os
import re

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


def code_to_identifier(x: str) -> str:
    x = x.upper()
    x = re.sub("[^A-Z0-9]+", "_", x)
    return x


def get_class_definitions(class_name: str, query: str) -> str:

    class_name_group = f"{class_name}s"
    df = sql_to_df(query)
    lines = [
        f"class {class_name_group}:",
    ]
    for item in df.to_dict(orient="records"):
        ident = code_to_identifier(item["code"])
        clsname = f"{class_name}{ident}"
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in item.items())
        line = f'    {ident} = {class_name}._create_subclass("{clsname}", {kwargs_str})'
        lines.append(line)

    return "\n".join(lines)


def get_class_instances(class_name: str, query: str) -> str:

    class_name_group = f"{class_name}s"
    df = sql_to_df(query)
    lines = [
        f"class {class_name_group}:",
    ]
    for item in df.to_dict(orient="records"):
        ident = code_to_identifier(item["code"])
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in item.items())
        line = f"    {ident} = {class_name}({kwargs_str})"
        lines.append(line)

    return "\n".join(lines)


def main():
    # header
    literals = [
        '"""DO NOT EDIT (created by classes/_update.py)."""',
        """from ptxboa.classes.base import (
            PtxboaParameter, PtxboaProcess, PtxboaFlow, PtxboaRegion
        )""",
    ]

    literals.append(
        get_class_definitions(
            "PtxboaParameter",
            """SELECT
            parameter_code AS code,
            parameter_name AS name,
            'PtxboaParameter' AS template_class_name
            FROM ptxboa_parameter ORDER BY parameter_code""",
        )
    )

    literals.append(
        get_class_definitions(
            "PtxboaProcess",
            """SELECT
            process_code AS code,
            process_name AS name,
            'PtxboaProcess' AS template_class_name
            FROM ptxboa_process ORDER BY process_code""",
        )
    )

    literals.append(
        get_class_definitions(
            "PtxboaFlow",
            """SELECT
            flow_code AS code,
            flow_name AS name,
            'PtxboaFlow' AS template_class_name
            FROM ptxboa_flow ORDER BY flow_code""",
        )
    )

    literals.append(
        get_class_instances(
            "PtxboaRegion",
            """SELECT
            region_code AS code,
            region_name AS name
            FROM ptxboa_source_region ORDER BY region_code""",
        )
    )

    with open(PYTHON_FILE, "w", encoding="utf-8") as file:
        for x in literals:
            file.write(x)
            file.write("\n\n")


if __name__ == "__main__":
    main()
