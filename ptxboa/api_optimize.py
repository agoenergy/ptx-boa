# -*- coding: utf-8 -*-
"""Data interface for optimized data of FLH."""

import datetime
import hashlib
import json
import os
import pickle  # noqa S403
import re
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from pypsa import Network

from flh_opt import __version__ as flh_opt_version
from flh_opt._types import OptInputDataType, OptOutputDataType, SecProcessInputDataType
from flh_opt.api_opt import optimize
from ptxboa import logger
from ptxboa.static._types import CalculateDataType
from ptxboa.utils import SingletonMeta, annuity, serialize_for_hashing


def get_data_hash_md5(key: object) -> str:
    """Create md5 hash of data.

    Parameters
    ----------
    key : object
        any json serializable object

    Returns
    -------
    str
        md5 hash of a standardized byte representation of the input data
    """
    # serialize to str, make sure to sort keys
    sdata = serialize_for_hashing(key)
    # to bytes (only bytes can be hashed)
    bdata = sdata.encode()
    # create hash
    hash_md5 = hashlib.md5(bdata).hexdigest()  # noqa: S324 (md5 is fine)

    logger.debug(f"HASH: {hash_md5} for: {sdata}")

    return hash_md5


class TempFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filepath_tmp = None  # create in __enter__

    def __enter__(self):
        # check existing files
        fid, path = tempfile.mkstemp()
        os.close(fid)
        self.filepath_tmp = path
        return self.filepath_tmp

    def __exit__(self, exc_type, exc_val, exc_tb):
        # move to filepath_tmp => filepath
        if not os.path.getsize(self.filepath_tmp):
            # file should have been written
            logger.warning(f"file was not properly written: {self.filepath_tmp}")
            os.remove(self.filepath_tmp)
            return
        elif os.path.exists(self.filepath):
            # file was created in the meantime?
            logger.info(f"file already exist: {self.filepath}")
            os.remove(self.filepath_tmp)
        else:
            # move file to target
            shutil.move(self.filepath_tmp, self.filepath)
            logger.info(f"saved file {self.filepath}")


class ProfilesHashes(metaclass=SingletonMeta):
    """Only instanciated once for path."""

    PATTERN = re.compile(
        r"^(?P<region>[^_]+)_(?P<res>.+)_aggregated.weights.csv.metadata.json$"
    )

    def __init__(self, profiles_path):
        self.profiles_path = str(profiles_path)
        self.data = self._load_all()

    def _read_metadata(self, filename):
        """Read metadata json file."""
        filepath = f"{self.profiles_path}/{filename}"
        logger.debug(f"READ {filepath}")
        with open(filepath, encoding="utf-8") as file:
            data = json.load(file)
        return data

    def _load_all(self) -> dict:
        """Load all metadata json files."""
        result = {}
        for filename in os.listdir(self.profiles_path):
            match = self.PATTERN.match(filename)
            if not match:
                continue
            # region_code, res_code not in metadata,so we
            # extract it from filename
            region_res = match.groups()
            metadata = self._read_metadata(filename) | match.groupdict()
            result[region_res] = metadata
        return result


class ProfilesFLH(metaclass=SingletonMeta):
    """Only instanciated once for profiles_path."""

    PATTERN = re.compile(r"^(?P<region>[^_]+)_(?P<res>.+)_aggregated.csv$")

    def __init__(self, profiles_path: Path):
        self.profiles_path = profiles_path
        self.data = self._load_all()

    def _available_profiles(self) -> list[tuple[str, str]]:
        region_res = []
        for f in self.profiles_path.iterdir():
            match = self.PATTERN.match(f.name)
            if not match:
                continue
            region_res.append(match.groups())
        return region_res

    def _load_all(self) -> dict:
        """Load all FLH data from profiles.

        Profiles need to be weighted first.
        """
        logger.info("load flh from profiles data")
        profile_data = []
        for region, res_location in self._available_profiles():
            profiles_file = (
                self.profiles_path / f"{region}_{res_location}_aggregated.csv"
            )
            weights_file = (
                self.profiles_path / f"{region}_{res_location}_aggregated.weights.csv"
            )
            pr = pd.read_csv(profiles_file, index_col=["period_id", "TimeStep"])
            we = pd.read_csv(weights_file, index_col=["period_id", "TimeStep"])
            # multiply columns in profiles with weightings
            pr_weighted = (
                pr.mul(we.squeeze(), axis=0)
                .reset_index(drop=True)
                .stack()
                .rename("specific_generation")
            )
            pr_weighted.index = pr_weighted.index.set_names("re_source", level=-1)
            pr_weighted = pr_weighted.reset_index()
            pr_weighted["re_location"] = res_location
            pr_weighted["source_region"] = region
            profile_data.append(pr_weighted)

        profile_data = pd.concat(profile_data)

        flh = (
            profile_data.groupby(["source_region", "re_location", "re_source"])[
                "specific_generation"
            ]
            .sum()
            .rename("value")
            .reset_index()
        )

        # combine re_location and re_source to res_gen code
        def combine_location_and_source(re_location, re_source):
            if re_location == re_source:
                return re_source
            else:
                return f"{re_location}-{re_source}"

        flh["res_gen"] = flh.apply(
            lambda x: combine_location_and_source(x["re_location"], x["re_source"]),
            axis=1,
        )

        return flh[["source_region", "res_gen", "value"]]


class PtxOpt:

    def __init__(self, profiles_path: Path, cache_dir: Path):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.profiles_hashes = ProfilesHashes(profiles_path)
        self.profiles_flh = ProfilesFLH(profiles_path)

    def _save(
        self, filepath: str, data: object, network: Network, metadata: dict
    ) -> None:

        filepath = str(filepath)

        with TempFile(filepath) as filepath_tmp:
            with open(filepath_tmp, "wb") as file:
                pickle.dump(data, file)

        # also save network
        filepath_nw = filepath + ".network.nc"
        with TempFile(filepath_nw) as filepath_tmp:
            network.export_to_netcdf(filepath_tmp)

        # also save metadata
        with TempFile(filepath + ".metadata.json") as filepath_tmp:
            with open(filepath_tmp, "w", encoding="utf-8") as file:
                json.dump(metadata, file, indent=2, ensure_ascii=False)

    def _load(self, filepath: str) -> object:
        with open(filepath, "rb") as file:
            data = pickle.load(file)  # noqa S301
        return data

    def _load_network(self, filepath: str):
        filepath_nw = str(filepath) + ".network.nc"

        network = Network()
        network.import_from_netcdf(filepath_nw)

        filepath_metadata = str(filepath) + ".metadata.json"
        with open(filepath_metadata, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        return network, metadata

    def _get_cache_filepath(self, hashsum: str, suffix=".pickle") -> str:
        # group twice by first two chars (256 combinations)
        dirpath = self.cache_dir / hashsum[0:2] / hashsum[2:4]
        os.makedirs(dirpath, exist_ok=True)
        filepath = dirpath / f"{hashsum}{suffix}"
        filepath = str(filepath.resolve())
        return filepath

    @staticmethod
    def _prepare_data(input_data: CalculateDataType) -> OptInputDataType:

        src_reg = input_data["context"]["source_region_code"]

        result = {
            "SOURCE_REGION_CODE": src_reg,
            "RES": [],
            "ELY": None,
            "DERIV": None,
            "SPECCOST": {
                "H2O-L": input_data["parameter"]["SPECCOST"]["H2O-L"],
                "CO2-G": input_data["parameter"]["SPECCOST"]["CO2-G"],
                "N2-G": input_data["parameter"]["SPECCOST"]["N2-G"],
                "HEAT": input_data["parameter"]["SPECCOST"]["HEAT"],
            },
            "EL_STR": None,
            "H2_STR": None,
            "CO2": None,
            "H2O": None,
        }

        for step in input_data["main_process_chain"]:
            if step["step"] == "RES":
                if step["process_code"] == "RES-HYBR":
                    for pc in ["PV-FIX", "WIND-ON"]:
                        proc_data = input_data["flh_opt_process"][pc]
                        result["RES"].append(
                            {
                                "CAPEX_A": annuity(
                                    periods=proc_data["LIFETIME"],
                                    rate=input_data["parameter"]["WACC"],
                                    value=proc_data["CAPEX"],
                                ),
                                "OPEX_F": proc_data["OPEX-F"],
                                "OPEX_O": proc_data["OPEX-O"],
                                "PROCESS_CODE": pc,
                            }
                        )
                else:
                    result["RES"].append(
                        {
                            "CAPEX_A": annuity(
                                periods=step["LIFETIME"],
                                rate=input_data["parameter"]["WACC"],
                                value=step["CAPEX"],
                            ),
                            "OPEX_F": step["OPEX-F"],
                            "OPEX_O": step["OPEX-O"],
                            "PROCESS_CODE": step["process_code"],
                        }
                    )

            elif step["step"] == "ELY":
                result["ELY"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "CONV": step["CONV"],
                }
            elif step["step"] == "DERIV":
                result["DERIV"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "PROCESS_CODE": step["process_code"],
                    "CONV": step["CONV"],
                }
            elif step["step"] in ("EL_STR", "H2_STR"):
                result[step["step"]] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                }

        # data for secondary processes
        for step, flow_code in [("H2O", "H2O-L"), ("CO2", "CO2-G")]:
            sec_process_data = input_data["secondary_process"].get(flow_code)
            if not sec_process_data:
                continue

            result_sec_process_data: SecProcessInputDataType = {
                "CAPEX_A": annuity(
                    periods=sec_process_data["LIFETIME"],
                    rate=input_data["parameter"]["WACC"],
                    value=sec_process_data["CAPEX"],
                ),
                "OPEX_F": sec_process_data["OPEX-F"],
                "OPEX_O": sec_process_data["OPEX-O"],
                "CONV": sec_process_data["CONV"],
            }
            result[step] = result_sec_process_data

        return result

    @staticmethod
    def _merge_data(input_data: CalculateDataType, opt_output_data: OptOutputDataType):
        flh_opt_process = input_data["flh_opt_process"]

        # only overwrite  flh if optimization was successful:
        if opt_output_data["model_status"][1] == "optimal":
            for step in input_data["main_process_chain"]:
                if step["step"] == "RES":
                    output_res = opt_output_data["RES"]
                    if step["process_code"] == "RES-HYBR":
                        assert len(output_res) == 2
                        step["FLH"] = sum(
                            x["FLH"] * x["SHARE_FACTOR"] for x in output_res
                        )
                        # Merge technologies with SHARE_FACTOR for each PROCESS_CODE
                        for k in ["LIFETIME", "CAPEX", "OPEX-F", "OPEX-O"]:
                            step[k] = sum(
                                flh_opt_process[x["PROCESS_CODE"]][k]
                                * x["SHARE_FACTOR"]
                                for x in output_res
                            )
                    else:
                        assert len(output_res) == 1
                        flh = output_res[0]["FLH"]
                        step["FLH"] = flh

                    step["FLH"] = step["FLH"] * 8760  # NOTE: output is fraction

                elif step["step"] == "ELY":
                    step["FLH"] = opt_output_data["ELY"]["FLH"] * 8760
                elif step["step"] == "DERIV":
                    step["FLH"] = opt_output_data["DERIV"]["FLH"] * 8760
                elif step["step"] == "EL_STR":
                    step["CAP_F"] = opt_output_data["EL_STR"]["CAP_F"]
                elif step["step"] == "H2_STR":
                    step["CAP_F"] = opt_output_data["H2_STR"]["CAP_F"]

            # secondary processes
            for step, flow_code in [("H2O", "H2O-L"), ("CO2", "CO2-G")]:
                sec_process_data = input_data["secondary_process"].get(flow_code)
                if not sec_process_data:
                    continue
                sec_process_data["FLH"] = opt_output_data[step]["FLH"] * 8760

        else:
            logger.warning("Optimization not successful.")
            logger.warning(f"Solver status:{opt_output_data['model_status'][0]}")
            logger.warning(f"Model status:{opt_output_data['model_status'][1]}")

    def _get_hashsum(self, data, opt_input_data):
        src_reg = data["context"]["source_region_code"]
        # find res
        res = None
        for step in data["main_process_chain"]:
            if step["step"] == "RES":
                res = step["process_code"]
                break

        key = (src_reg, res)
        try:
            profiles_filehash_md5 = self.profiles_hashes.data[key]["filehash_md5"]
        except KeyError:
            # raise more descriptive error
            raise KeyError("No profiles data exists for region=%s, RES=%s." % key)

        hash_data = {
            "opt_input_data": opt_input_data,
            # data not needed for optimization
            # but that should change the hash
            "context": {
                "flh_opt_version": flh_opt_version,
                "profiles_filehash_md5": profiles_filehash_md5,
            },
        }
        hashsum = get_data_hash_md5(hash_data)
        return hash_data, hashsum

    def get_data(
        self, data_opt: CalculateDataType, data: CalculateDataType
    ) -> CalculateDataType:
        """Get calculation data including optimized FLH.

        Parameters
        ----------
        data : CalculateDataType
            input data

        Returns
        -------
        CalculateDataType
            same data, but replaced FLH (and some other data points)
            with results from optimization
        """
        # prepare data for optimization
        # (even if we dont optimize, we needit to get hashsum)
        opt_input_data = self._prepare_data(data_opt)

        use_cache = bool(self.cache_dir)

        # get hashsum (and metadata opt metadata)
        opt_metadata, hash_sum = self._get_hashsum(data_opt, opt_input_data)

        if use_cache:
            hash_filepath = self._get_cache_filepath(hash_sum)
        else:
            hash_filepath = None

        cache_exists = use_cache and os.path.exists(hash_filepath)

        if not cache_exists:
            # must run optimizer
            logger.info(f"Run new optimizazion: {hash_sum}")
            logger.debug(hash_filepath)
            logger.debug(opt_input_data)

            opt_output_data, network = optimize(
                opt_input_data, profiles_path=self.profiles_hashes.profiles_path
            )
            opt_metadata["model_status"] = opt_output_data["model_status"]
            opt_metadata["datetime"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if use_cache:
                # save results
                self._save(hash_filepath, opt_output_data, network, opt_metadata)
        else:
            # load existing results
            opt_output_data = self._load(hash_filepath)

        self._merge_data(data, opt_output_data)

        # also add flh_opt_hash if it exists so we can
        # retrieve the network later
        if use_cache:
            data["flh_opt_hash"] = {
                "hash_md5": hash_sum,
                "filepath": hash_filepath,
            }
        else:
            data["flh_opt_hash"] = {
                "hash_md5": hash_sum,
            }

        return data
