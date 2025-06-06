"""
Author: Lili Yu
Date: 2025-02-18 18:00:00
LastEditTime: 2025-02-18 18:00:00
LastEditors: Lili Yu
Description:
"""

import os
import logging
import collections
import pandas as pd
import numpy as np
from typing import Union
from tqdm import tqdm
import re
from hydroutils import hydro_time
from hydrodataset import CACHE_DIR, CAMELS_REGIONS
from hydrodataset.camels import Camels, time_intersect_dynamic_data

CAMELS_NO_DATASET_ERROR_LOG = (
    "We cannot read this dataset now. Please check if you choose correctly:\n"
    + str(CAMELS_REGIONS)
)

camelsgb_arg = {
    "forcing_type": "observation",
    "gauge_id_tag": "ID",
    "area_tag": ["Area_km2", ],
    "meanprcp_unit_tag": [["Pmean_mm_year"], "mm/yr"],
    "time_range": {
        "observation": ["1961-01-01", "2021-01-01"],
    },
    "target_cols": ["Qobs_m3s", "Qobs_mm"],
    "b_nestedness": False,
    "forcing_unit": ["mm/day", "°C",],
    "data_file_attr": {
        "sep": ",",
        "header": 0,
        "attr_file_str": ["catchments_", ".csv", ]
    },
}

class CamelsSe(Camels):
    def __init__(
        self,
        data_path = os.path.join("camels","camels_se"),
        download = False,
        region: str = "SE",
        arg: dict = camelsgb_arg,
    ):
        """
        Initialization for CAMELS-SE dataset

        Parameters
        ----------
        data_path
            where we put the dataset.
            we already set the ROOT directory for hydrodataset,
            so here just set it as a relative path,
            by default "camels/camels_se"
        download
            if true, download, by default False
        region
            the default is CAMELS-SE
        """
        super().__init__(data_path, download, region, arg)

    def _set_data_source_camels_describe(self, camels_db):
        # shp file of basins
        camels_shp_file = camels_db.joinpath(
            "catchment_GIS_shapefiles",
            "catchment_GIS_shapefiles",
            "Sweden_catchments_50_boundaries_WGS84.shp",
        )
        # flow and forcing data are in a same file
        flow_dir = camels_db.joinpath(
            "catchment time series",
            "catchment time series",
        )
        forcing_dir = flow_dir
        # attr
        attr_dir = camels_db.joinpath(
            "catchment properties",
            "catchment properties",
        )
        attr_key_lst = [
            "hydrological_signatures_1961_2020",
            "landcover",
            "physical_properties",
            "soil_classes",
        ]
        gauge_id_file = attr_dir.joinpath("catchments_physical_properties.csv")
        nestedness_information_file = None
        base_url = "https://api.researchdata.se/dataset/2023-173/1/"
        download_url_lst = [
            f"{base_url}/file/data?filePath=catchment+properties.zip",
            f"{base_url}/file/data?filePath=catchment+time+series.zip",
            f"{base_url}/file/data?filePath=catchment_GIS_shapefiles.zip",
        ]

        return collections.OrderedDict(
            CAMELS_DIR = camels_db,
            CAMELS_FLOW_DIR = flow_dir,
            CAMELS_FORCING_DIR = forcing_dir,
            CAMELS_ATTR_DIR = attr_dir,
            CAMELS_ATTR_KEY_LST = attr_key_lst,
            CAMELS_GAUGE_FILE = gauge_id_file,
            CAMELS_NESTEDNESS_FILE=nestedness_information_file,
            CAMELS_BASINS_SHP = camels_shp_file,
            CAMELS_DOWNLOAD_URL_LST=download_url_lst,
        )

    def get_constant_cols(self) -> np.ndarray:
        """
        all readable attrs in CAMELS-SE

        Returns
        -------
        np.ndarray
            attribute types
        """
        data_folder = self.data_source_description["CAMELS_ATTR_DIR"]
        return self._get_constant_cols_some(
            data_folder, "catchments_",".csv",","
        )

    def get_relevant_cols(self) -> np.ndarray:
        """
        all readable forcing types in CAMELS-SE

        Returns
        -------
        np.ndarray
            forcing types
        """
        return np.array(
            [
                "Pobs_mm",
                "Tobs_C",
            ]
        )

    def read_se_gage_flow_forcing(self, gage_id, t_range, var_type):
        """
        Read gage's streamflow or forcing from CAMELS-SE

        Parameters
        ----------
        gage_id
            the station id
        t_range
            the time range, for example, ["1961-01-01", "2021-01-01"]
        var_type
            flow type: "Qobs_m3s", "Qobs_mm"
            forcing type: "Pobs_mm","Tobs_C"

        Returns
        -------
        np.array
            streamflow or forcing data of one station for a given time range
        """
        logging.debug("reading %s streamflow data", gage_id)
        # use regular expressions for filename fuzzy matching
        pattern = r'catchment_id_' + gage_id + r'_.*\.csv'
        regex = re.compile(pattern)
        match_file = ""
        for filename in os.listdir(self.data_source_description["CAMELS_FLOW_DIR"]):
            if regex.search(filename):
                match_file = filename
        gage_file = os.path.join(
            self.data_source_description["CAMELS_FLOW_DIR"],
            match_file,
        )
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"])
        obs = data_temp[var_type].values
        if var_type in self.target_cols:
            obs[obs < 0] = np.nan
        df_date = data_temp[["Year", "Month", "Day"]]
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
        read target values. for CAMELS-SE, they are streamflows.

        default target_cols is an one-value list
        Notice, the unit of target outputs in different regions are not totally same

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1961-01-01", "2021-01-01"]
        target_cols
            the default is None, but we need at least one default target.
            For CAMELS-SE, it's ["Qobs_m3s"]
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
            range(len(target_cols)), desc="Read streamflow data of CAMELS-SE"
        ):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_se_gage_flow_forcing(
                    gage_id_lst[k], t_range, target_cols[j]
                )
                y[k, :, j] = data_obs
        # Keep unit of streamflow unified: we use ft3/s here
        # other units are m3/s -> ft3/s
        y = self.unit_convert_streamflow_m3tofoot3(y)
        return y

    def read_relevant_cols(
        self,
        gage_id_lst: list = None,
        t_range: list = None,
        var_lst: list = None,
        forcing_type="obs",
        **kwargs,
    ) -> np.ndarray:
        """
        Read forcing data

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1961-01-01", "2021-01-01"]
        var_lst
            forcing variable type: "Pobs_mm","Tobs_C"
        forcing_type
            support for CAMELS-SE, there are one types: obs
        Returns
        -------
        np.array
            forcing data
        """
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        x = np.full([len(gage_id_lst), nt, len(var_lst)], np.nan)
        for j in tqdm(range(len(var_lst)), desc="Read forcing data of CAMELS-SE"):
            for k in tqdm(range(len(gage_id_lst))):
                data_forcing = self.read_se_gage_flow_forcing(
                    gage_id_lst[k], t_range, var_lst[j]
                )
                x[k, :, j] = data_forcing
        return x

    def get_attribute_units_dict(self):
        """

        Returns
        -------

        """
        # # delete the repetitive attribute item, "Water_percentage".
        # duplicate_columns = attrs_df.columns[attrs_df.columns.duplicated()]
        # if duplicate_columns.size > 0:
        #     attrs_df = attrs_df.loc[:, ~attrs_df.columns.duplicated()]

        units_dict = {
            "S01_Qmean": "mm/year",
            "S02_Qcoeff": "percent",
            "S03_COM": "dimensionless",
            "S04_SPD": "dimensionless",
            "S05_Qmean_spring": "mm/season",
            "S06_Qmean_summer": "mm/season",
            "S07_Qmean_autumn": "mm/season",
            "S08_Qmean_winter": "mm/season",
            "S09_LFfreq": "days/year",
            "S10_T_minQ_d30": "days",
            "S11_minQ_d7": "mm",
            "S12_minQ_d30": "mm",
            "S13_HFfreq": "days/year",
            "S14_T_maxQ_d1": "dimensionless",
            "S15_maxQ_d30": "mm",
            "S16_maxQ_d1": "mm",
            "Urban_percentage": "percent",
            "Water_percentage": "percent",
            "Forest_percentage": "percent",
            "Open_land_percentage": "percent",
            "Agriculture_percentage": "percent",
            "Glaciers_percentage": "percent",
            "Shrubs_and_grassland_percentage": "percent",
            "Wetlands_percentage": "percent",
            "Name": "dimensionless",
            "Latitude_WGS84": "degree N",
            "Longitude_WGS84": "degree E",
            "Area_km2": "km^2",
            "Elevation_mabsl": "m.a.s.l.",
            "Slope_mean_degree": "degree",
            "DOR": "percent",
            "RegVol_m3": "m^3",
            "Pmean_mm_year": "mm/yr",
            "Tmean_C": "Celsius degree",
            "Glaciofluvial_sediment_percentage": "percent",
            "Bedrock_percentage": "percent",
            "Postglacial_sand_and_gravel_percentage": "percent",
            "Till_percentage": "percent",
            "Peat_percentage": "percent",
            "Silt_percentage": "percent",
            "Clayey_till_and_clay_till_percentage": "percent",
            "Till_and_weathered_deposit_percentage": "percent",
            "Glacier_percentage": "percent",
        }

        return units_dict
