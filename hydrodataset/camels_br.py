import logging
import os
import collections
import pandas as pd
import numpy as np
from typing import Union
from tqdm import tqdm
import xarray as xr
from hydroutils import hydro_time
from hydrodataset import CACHE_DIR, CAMELS_REGIONS
from hydrodataset.camels import Camels, time_intersect_dynamic_data
import json

CAMELS_NO_DATASET_ERROR_LOG = (
    "We cannot read this dataset now. Please check if you choose correctly:\n"
    + str(CAMELS_REGIONS)
)

camelsbr_arg = {
    "forcing_type": "observation",
    "gauge_id_tag": "gauge_id",
    "area_tag": ["area", ],
    "meanprcp_unit_tag": [["p_mean"], "mm/d"],
    "time_range": {
        "observation": ["1995-01-01", "2015-01-01"],
    },
    "target_cols": ["streamflow_mm_selected_catchments"],
    "b_nestedness": False,
    "forcing_unit": ["mm/d", "mm/d", "mm/d", "mm/d", "mm/d", "mm/d", "°C", "°C", "°C"],
    "data_file_attr": {
        "sep": r"\s+",
        "header": 0,
        "attr_file_str": ["camels_br_", ".txt", ]
    },
}

class CamelsBr(Camels):
    def __init__(
        self,
        data_path=os.path.join("camels", "camels_br"),
        download=False,
        region: str = "BR",
        arg: dict = camelsbr_arg,
    ):
        """
        Initialization for CAMELS-BR dataset

        Parameters
        ----------
        data_path
            where we put the dataset.
            we already set the ROOT directory for hydrodataset,
            so here just set it as a relative path,
            by default "camels/camels_br"
        download
            if true, download, by default False
        region
            the default is CAMELS-BR
        """
        super().__init__(data_path, download, region, arg)

    def _set_data_source_camels_describe(self, camels_db):
        # attr
        attr_dir = camels_db.joinpath(
            "01_CAMELS_BR_attributes", "01_CAMELS_BR_attributes"
        )
        # we don't need the location attr file
        attr_key_lst = [
            "climate",
            "geology",
            "human_intervention",
            "hydrology",
            "land_cover",
            "quality_check",
            "soil",
            "topography",
        ]
        # id and name, there are two types stations in CAMELS_BR, and we only chose the 897-stations version
        gauge_id_file = attr_dir.joinpath("camels_br_topography.txt")
        # shp file of basins
        camels_shp_file = camels_db.joinpath(
            "14_CAMELS_BR_catchment_boundaries",
            "14_CAMELS_BR_catchment_boundaries",
            "camels_br_catchments.shp",
        )
        # config of flow data
        # flow_dir_m3s = camels_db.joinpath(
        #     "02_CAMELS_BR_streamflow_m3s", "02_CAMELS_BR_streamflow_m3s"
        # )
        flow_dir_mm_selected_catchments = camels_db.joinpath(
            "03_CAMELS_BR_streamflow_mm_selected_catchments",
            "03_CAMELS_BR_streamflow_mm_selected_catchments",
        )
        # flow_dir_simulated = camels_db.joinpath(
        #     "04_CAMELS_BR_streamflow_simulated",
        #     "04_CAMELS_BR_streamflow_simulated",
        # )

        # forcing
        forcing_dir_precipitation_chirps = camels_db.joinpath(
            "05_CAMELS_BR_precipitation_chirps",
            "05_CAMELS_BR_precipitation_chirps",
        )
        forcing_dir_precipitation_mswep = camels_db.joinpath(
            "06_CAMELS_BR_precipitation_mswep",
            "06_CAMELS_BR_precipitation_mswep",
        )
        forcing_dir_precipitation_cpc = camels_db.joinpath(
            "07_CAMELS_BR_precipitation_cpc",
            "07_CAMELS_BR_precipitation_cpc",
        )
        forcing_dir_evapotransp_gleam = camels_db.joinpath(
            "08_CAMELS_BR_evapotransp_gleam",
            "08_CAMELS_BR_evapotransp_gleam",
        )
        forcing_dir_evapotransp_mgb = camels_db.joinpath(
            "09_CAMELS_BR_evapotransp_mgb",
            "09_CAMELS_BR_evapotransp_mgb",
        )
        forcing_dir_potential_evapotransp_gleam = camels_db.joinpath(
            "10_CAMELS_BR_potential_evapotransp_gleam",
            "10_CAMELS_BR_potential_evapotransp_gleam",
        )
        forcing_dir_temperature_min_cpc = camels_db.joinpath(
            "11_CAMELS_BR_temperature_min_cpc",
            "11_CAMELS_BR_temperature_min_cpc",
        )
        forcing_dir_temperature_mean_cpc = camels_db.joinpath(
            "12_CAMELS_BR_temperature_mean_cpc",
            "12_CAMELS_BR_temperature_mean_cpc",
        )
        forcing_dir_temperature_max_cpc = camels_db.joinpath(
            "13_CAMELS_BR_temperature_max_cpc",
            "13_CAMELS_BR_temperature_max_cpc",
        )
        nestedness_information_file = None
        base_url = "https://zenodo.org/records/15025488"
        download_url_lst = [
            f"{base_url}/files/01_CAMELS_BR_attributes.zip",
            f"{base_url}/files/02_CAMELS_BR_streamflow_all_catchments.zip",
            f"{base_url}/files/03_CAMELS_BR_streamflow_selected_catchments.zip",
            f"{base_url}/files/04_CAMELS_BR_streamflow_simulated.zip",
            f"{base_url}/files/05_CAMELS_BR_precipitation.zip",
            f"{base_url}/files/06_CAMELS_BR_actual_evapotransp.zip",
            f"{base_url}/files/07_CAMELS_BR_potential_evapotransp.zip",
            f"{base_url}/files/08_CAMELS_BR_reference_evapotransp.zip",
            f"{base_url}/files/09_CAMELS_BR_temperature.zip",
            f"{base_url}/files/10_CAMELS_BR_soil_moisture.zip",
            f"{base_url}/files/11_CAMELS_BR_precipitation_ana_gauges.zip",
            f"{base_url}/files/12_CAMELS_BR_catchment_boundaries.zip",
            f"{base_url}/files/13_CAMELS_BR_gauge_location.zip",
            f"{base_url}/files/CAMELS_BR_readme.txt",
        ]

        return collections.OrderedDict(
            CAMELS_DIR=camels_db,
            CAMELS_FLOW_DIR=[
                # flow_dir_m3s,
                flow_dir_mm_selected_catchments,
                # flow_dir_simulated,
            ],
            CAMELS_FORCING_DIR=[
                forcing_dir_precipitation_chirps,
                forcing_dir_precipitation_mswep,
                forcing_dir_precipitation_cpc,
                forcing_dir_evapotransp_gleam,
                forcing_dir_evapotransp_mgb,
                forcing_dir_potential_evapotransp_gleam,
                forcing_dir_temperature_min_cpc,
                forcing_dir_temperature_mean_cpc,
                forcing_dir_temperature_max_cpc,
            ],
            CAMELS_ATTR_DIR=attr_dir,
            CAMELS_ATTR_KEY_LST=attr_key_lst,
            CAMELS_GAUGE_FILE=gauge_id_file,
            CAMELS_NESTEDNESS_FILE=nestedness_information_file,
            CAMELS_BASINS_SHP_FILE=camels_shp_file,
            CAMELS_DOWNLOAD_URL_LST=download_url_lst,
        )

    def get_constant_cols(self) -> np.ndarray:
        """
        all readable attrs in CAMELS-BR

        Returns
        -------
        np.array
            attribute types
        """
        data_folder = self.data_source_description["CAMELS_ATTR_DIR"]
        return self._get_constant_cols_some(data_folder, "camels_br_", ".txt", "\s+")

    def get_relevant_cols(self) -> np.ndarray:
        """
        all readable forcing types in CAMELS-BR

        Returns
        -------
        np.array
            forcing types
        """
        return np.array(
            [
                str(forcing_dir).split(os.sep)[-1][13:]
                for forcing_dir in self.data_source_description["CAMELS_FORCING_DIR"]
            ]
        )

    def read_br_gage_flow(self, gage_id, t_range, flow_type):
        """
        Read gage's streamflow from CAMELS-BR

        Parameters
        ----------
        gage_id
            the station id
        t_range
            the time range, for example, ["1995-01-01", "2015-01-01"]
        flow_type
            "streamflow_m3s" or "streamflow_mm_selected_catchments" or "streamflow_simulated"

        Returns
        -------
        np.array
            streamflow data of one station for a given time range
        """
        logging.debug("reading %s streamflow data", gage_id)
        dir_ = [
            str(flow_dir)
            for flow_dir in self.data_source_description["CAMELS_FLOW_DIR"]
            if flow_type in str(flow_dir)
        ][0]
        if flow_type == "streamflow_mm_selected_catchments":
            flow_type = "streamflow_mm"
        # elif flow_type == "streamflow_simulated":
        #     flow_type = "simulated_streamflow"
        gage_file = os.path.join(dir_, gage_id + "_" + flow_type + ".txt")
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"])
        obs = data_temp.iloc[:, 3].values
        obs[obs < 0] = np.nan
        df_date = data_temp[["year", "month", "day"]]
        date = pd.to_datetime(df_date).values.astype("datetime64[D]")
        return time_intersect_dynamic_data(obs, date, t_range)

    def read_target_cols(
        self,
        gage_id_lst: Union[list, np.array] = None,
        t_range: list = None,
        target_cols: Union[list, np.array] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        read target values; for CAMELS-BR, they are streamflows

        default target_cols is an one-value list
        Notice: the unit of target outputs in different regions are not totally same

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1995-01-01", "2015-01-01"]
        target_cols
            the default is None, but we need at least one default target.
            For CAMELS-BR, it's ["streamflow_mmd"]
        kwargs
            some other params if needed

        Returns
        -------
        np.array
            streamflow data, 3-dim [station, time, streamflow]
        """
        if target_cols is None:
            return np.array([])
        else:
            nf = len(target_cols)
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        y = np.full([len(gage_id_lst), nt, nf], np.nan)
        for j in tqdm(
            range(len(target_cols)), desc="Read streamflow data of CAMELS-BR"
        ):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_br_gage_flow(
                    gage_id_lst[k], t_range, target_cols[j]
                )
                y[k, :, j] = data_obs
        # Keep unit of streamflow unified: we use ft3/s here
        # other units are m3/s -> ft3/s
        y = self.unit_convert_streamflow_m3tofoot3(y)
        return y

    def read_br_basin_forcing(self, gage_id, t_range, var_type) -> np.array:
        """
        Read one forcing data for a basin in CAMELS_BR

        Parameters
        ----------
        gage_id
            basin id
        t_range
            the time range, for example, ["1995-01-01", "2005-01-01"]
        var_type
            the forcing variable type, "precipitation_chirps", "precipitation_mswep", "precipitation_cpc", "evapotransp_gleam", "evapotransp_mgb",
                   "potential_evapotransp_gleam", "temperature_min_cpc", "temperature_mean_cpc", "temperature_max_cpc"

        Returns
        -------
        np.array
            one type forcing data of a basin in a given time range
        """
        dir_ = [
            str(_dir)
            for _dir in self.data_source_description["CAMELS_FORCING_DIR"]
            if var_type in str(_dir)
        ][0]
        if var_type in [
            "temperature_min_cpc",
            "temperature_mean_cpc",
            "temperature_max_cpc",
        ]:
            var_type = var_type[:-4]
        gage_file = os.path.join(dir_, gage_id + "_" + var_type + ".txt")
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"])
        obs = data_temp.iloc[:, 3].values
        df_date = data_temp[["year", "month", "day"]]
        date = pd.to_datetime(df_date).values.astype("datetime64[D]")
        return time_intersect_dynamic_data(obs, date, t_range)

    def read_relevant_cols(
        self,
        gage_id_lst: list = None,
        t_range: list = None,
        var_lst: list = None,
        forcing_type="daymet",
        **kwargs,
    ) -> np.ndarray:
        """
        Read forcing data

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1995-01-01", "2015-01-01"]
        var_lst
            forcing variable types
        forcing_type
            now only for CAMELS-BR, there are only one type: observation
        Returns
        -------
        np.array
            forcing data
        """
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        x = np.full([len(gage_id_lst), nt, len(var_lst)], np.nan)
        for j in tqdm(range(len(var_lst)), desc="Read forcing data of CAMELS-BR"):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_br_basin_forcing(
                    gage_id_lst[k], t_range, var_lst[j]
                )
                x[k, :, j] = data_obs
        return x

    def get_attribute_units_dict(self):
        """

        Returns
        -------

        """
        units_dict = {
            "p_mean": "mm/day",
            "pet_mean": "mm/day",
            "et_mean": "mm/day",
            "aridity": "dimensionless",
            "p_seasonality": "dimensionless",
            "asynchronicity": "dimensionless",
            "frac_snow": "dimensionless",
            "high_prec_freq": "days/yr",
            "high_prec_dur": "days",
            "high_prec_timing": "season",
            "low_prec_freq": "days/yr",
            "low_prec_dur": "days",
            "low_prec_timing": "season",
            "geol_class_1st": "dimensionless",
            "geol_class_1st_perc": "percent",
            "geol_class_2nd": "dimensionless",
            "geol_class_2nd_perc": "percent",
            "carb_rocks_perc": "percent",
            "geol_porosity": "dimensionless",
            "geol_permeability": "m^2",
            "consumptive_use": "mm/yr",
            "consumptive_use_perc": "percent",
            "reservoirs_vol": "10^6 m^3",
            "regulation_degree": "percent",
            "q_mean": "mm/day",
            "runoff_ratio": "dimensionless",
            "stream_elas": "dimensionless",
            "slope_fdc": "dimensionless",
            "baseflow_index": "dimensionless",
            "hfd_mean": "day of the year",
            "Q5": "mm/day",
            "Q95": "mm/day",
            "high_q_freq": "days/yr",
            "high_q_dur": "days",
            "low_q_freq": "days/yr",
            "low_q_dur": "days",
            "zero_q_freq": "days/yr",
            "crop_perc": "percent",
            "crop_mosaic_perc": "percent",
            "forest_perc": "percent",
            "shrub_perc": "percent",
            "grass_perc": "percent",
            "barren_perc": "percent",
            "imperv_perc": "percent",
            "wet_perc": "percent",
            "snow_perc": "percent",
            "dom_land_cover": "dimensionless",
            "dom_land_cover_perc": "percent",
            "gauge_name": "dimensionless",
            "gauge_region": "dimensionless",
            "gauge_lat": "degree North",
            "gauge_lon": "degree East",
            "area_ana": "km^2",
            "area_gsim": "km^2",
            "area_gsim_quality": "km^2",
            "q_quality_control_perc": "percent",
            "q_stream_stage_perc": "percent",
            "sand_perc": "percent",
            "silt_perc": "percent",
            "clay_perc": "percent",
            "org_carbon_content": "g/kg",
            "bedrock_depth": "cm",
            "water_table_depth": "cm",
            "elev_gauge": "m.a.s.l.",
            "elev_mean": "m.a.s.l.",
            "slope_mean": "m/km",
            "area": "km^2",
        }

        return units_dict

    def cache_streamflow_xrdataset(self):
        """Save all basins' streamflow data in a netcdf file in the cache directory

        """
        cache_npy_file = CACHE_DIR.joinpath("camels_br_streamflow.npy")
        json_file = CACHE_DIR.joinpath("camels_br_streamflow.json")
        if (not os.path.isfile(cache_npy_file)) or (not os.path.isfile(json_file)):
            self.cache_streamflow_np_json()
        streamflow = np.load(cache_npy_file)
        with open(json_file, "r") as fp:
            streamflow_dict = json.load(fp, object_pairs_hook=collections.OrderedDict)
        import pint_xarray

        basins = streamflow_dict["basin"]
        times = pd.date_range(
            streamflow_dict["time"][0], periods=len(streamflow_dict["time"])
        )
        return xr.Dataset(
            {
                "streamflow": (
                    ["basin", "time"],
                    streamflow[:, :, 0],
                    {"units": self.streamflow_unit},
                ),
                # "ET": (
                #     ["basin", "time"],
                #     streamflow[:, :, 1],
                #     {"units": "mm/day"},
                # ),
            },
            coords={
                "basin": basins,
                "time": times,
            },
        )
