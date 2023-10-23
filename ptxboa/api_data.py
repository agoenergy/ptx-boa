# -*- coding: utf-8 -*-
"""Handle data queries for api calculation."""


class ApiData:
    def __init__(self):
        ...

    def get_parameter_value(
        parameter_code,
        process_code=None,  # process_flh for flh
        flow_code=None,
        source_region_code=None,
        target_country_code=None,
        # only relevant for parameter FLH
        process_code_res=None,
        process_code_ely=None,
        process_code_deriv=None,
    ) -> float:
        """Get parameter value for processes."""
        ...
