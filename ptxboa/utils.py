# -*- coding: utf-8 -*-
"""Helper functions."""

from typing import Dict, List

from ptxboa.data.static import (
    FlowCodeType,
    ProcessCodeType,
    ProcessStepType,
    SourceRegionCodeType,
    TargetCountryCodeType,
)


def annuity(rate: float, periods: int, value: float) -> float:
    """Calculate annuity.

    Parameters
    ----------
    rate: float
        interest rate per period
    periods: int
        number of periods
    value: float
        present value of an ordinary annuity

    Returns
    -------
    : float
        value of each payment

    """
    if rate == 0:
        return value / periods
    else:
        return value * rate / (1 - (1 / (1 + rate) ** periods))


def get_transport_distances(
    source_region_code: SourceRegionCodeType,
    target_country_code: TargetCountryCodeType,
    use_ship: bool,
    ship_own_fuel: bool,
    dist_ship: float,
    dist_pipeline: float,
    seashare_pipeline: float,
    existing_pipeline_cap: float,
) -> Dict[ProcessStepType, float]:
    # TODO: new calculation of distances
    dist_transp = {}
    if source_region_code == target_country_code:
        # no transport (only China)
        pass
    elif dist_pipeline and not use_ship:
        # use pipeline if pipeline possible and ship not selected
        if existing_pipeline_cap:
            # use retrofitting
            dist_transp["PPLX"] = dist_pipeline * seashare_pipeline
            dist_transp["PPLR"] = dist_pipeline * (1 - seashare_pipeline)
        else:
            dist_transp["PPLS"] = dist_pipeline * seashare_pipeline
            dist_transp["PPL"] = dist_pipeline * (1 - seashare_pipeline)
    else:
        # use ship
        if ship_own_fuel:
            dist_transp["SHP-OWN"] = dist_ship
        else:
            dist_transp["SHP"] = dist_ship

    return dist_transp


def _validate_process_chain(
    DataHandler, process_codes: List[ProcessCodeType], final_flow_code: FlowCodeType
) -> None:
    df_processes = DataHandler.get_dimension("process")
    flow_code = ""  # initial flow code
    for process_code in process_codes:
        process = df_processes.loc[process_code]
        flow_code_in = process["main_flow_code_in"]
        assert flow_code == flow_code_in
        flow_code = process["main_flow_code_out"]
    assert flow_code == final_flow_code


def filter_chain_processes(
    DataHandler, chain: dict, transport_distances: Dict[ProcessStepType, float]
) -> List[ProcessStepType]:
    result_main = []
    result_transport = []
    for process_step in ["RES", "ELY", "DERIV"]:
        process_code = chain[process_step]
        if process_code:
            result_main.append(process_step)
    is_shipping = transport_distances.get("SHP") or transport_distances.get("SHP-OWN")
    is_pipeline = (
        transport_distances.get("PPLS")
        or transport_distances.get("PPL")
        or transport_distances.get("PPLX")
        or transport_distances.get("PPLR")
    )
    if is_shipping:
        if chain["PRE_SHP"]:  # not all have preprocessing
            result_transport.append("PRE_SHP")
    elif is_pipeline:
        if chain["PRE_PPL"]:  # not all have preprocessing
            result_transport.append("PRE_PPL")

    for k, v in transport_distances.items():
        if v:
            assert chain[k]
            result_transport.append(k)

    if is_shipping:
        if chain["POST_SHP"]:  # not all have preprocessing
            result_transport.append("POST_SHP")
    elif is_pipeline:
        if chain["POST_PPL"]:  # not all have preprocessing
            result_transport.append("POST_PPL")

    # TODO: CHECK that flow chain is correct
    _validate_process_chain(
        DataHandler,
        [chain[p] for p in result_main + result_transport],
        chain["FLOW_OUT"],
    )

    return result_main, result_transport
