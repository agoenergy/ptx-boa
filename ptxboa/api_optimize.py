# -*- coding: utf-8 -*-
"""Data interface for optimized data of FLH."""

import datetime
import hashlib
import json
import os
import pickle  # noqa S403
import re
from pathlib import Path

from pypsa import Network

from flh_opt import __version__ as flh_opt_version
from flh_opt._types import OptInputDataType, OptOutputDataType
from flh_opt.api_opt import optimize
from ptxboa import logger
from ptxboa.static._types import CalculateDataType
from ptxboa.utils import SingletonMeta, annuity


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
    sdata = json.dumps(key, sort_keys=True, ensure_ascii=False, indent=0)
    # to bytes (only bytes can be hashed)
    bdata = sdata.encode()
    # create hash
    hash_md5 = hashlib.md5(bdata).hexdigest()  # noqa: S324 (md5 is fine)
    return hash_md5


class TempFile:
    def __init__(self, filepath, raise_on_overwrite=False):
        self.filepath = filepath
        self.filepath_tmp = str(self.filepath) + ".tmp"
        self.raise_on_overwrite = raise_on_overwrite

    def __enter__(self):
        # check existing files
        for path in [self.filepath, self.filepath_tmp]:
            if os.path.exists(path):
                message = f"file should not exist - overwriting: {path}"
                if self.raise_on_overwrite:
                    raise FileExistsError(message)
                logger.warning(message)
                os.remove(path)
        return self.filepath_tmp

    def __exit__(self, exc_type, exc_val, exc_tb):
        # move to filepath_tmp => filepath
        if not os.path.exists(self.filepath_tmp):
            # file should have been written
            logger.warning(f"file does not exist: {self.filepath_tmp}")
            return
        if os.path.exists(self.filepath):
            # file was created in the meantime?
            logger.warning(f"file should not exist - overwriting: {self.filepath}")
            os.remove(self.filepath)
        if exc_type:
            # there was an error: remove temporary file
            os.remove(self.filepath_tmp)
            logger.warning(exc_val)  # or raise Error
        else:
            # move file to target
            os.rename(self.filepath_tmp, self.filepath)
            logger.debug(f"saved file {self.filepath}")


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


class PtxOpt:

    def __init__(self, profiles_path: Path, cache_dir: Path):
        self.cache_dir = cache_dir
        self.profiles_hashes = ProfilesHashes(profiles_path)

    def _save(
        self,
        filepath: str,
        data: object,
        network: Network,
        metadata: dict,
        raise_on_overwrite=False,
    ) -> None:
        with TempFile(filepath, raise_on_overwrite=raise_on_overwrite) as filepath_tmp:
            with open(filepath_tmp, "wb") as file:
                pickle.dump(data, file)

        # also save network
        filepath_nw = str(filepath) + ".network.nc"
        with TempFile(filepath_nw, raise_on_overwrite=False) as filepath_tmp:
            network.export_to_netcdf(filepath_tmp)

        # also save metadata
        filepath_metadata = str(filepath) + ".metadata.json"
        with open(filepath_metadata, "w", encoding="utf-8") as file:
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
        else:
            logger.warning("Optimization not successful.")
            logger.warning(f"Solver status:{opt_output_data['model_status'][0]}")
            logger.warning(f"Model status:{opt_output_data['model_status'][1]}")

            # TODO: Storage: "CAP_F"

    def _get_hashsum(self, data, opt_input_data):
        src_reg = data["context"]["source_region_code"]
        # find res
        res = None
        for step in data["main_process_chain"]:
            if step["step"] == "RES":
                res = step["process_code"]
                break

        key = (src_reg, res)
        profiles_filehash_md5 = self.profiles_hashes.data[key]["filehash_md5"]

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

    def get_data(self, data: CalculateDataType) -> CalculateDataType:
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
        opt_input_data = self._prepare_data(data)

        use_cache = bool(self.cache_dir)

        # get hashsum (and metadata opt metadata)
        opt_metadata, hash_sum = self._get_hashsum(data, opt_input_data)

        if use_cache:
            hash_filepath = self._get_cache_filepath(hash_sum)
        else:
            hash_filepath = None

        cache_exists = use_cache and os.path.exists(hash_filepath)

        if not cache_exists:
            # must run optimizer
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
