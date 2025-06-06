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
from hydroutils import hydro_time
from hydrodataset import CACHE_DIR, CAMELS_REGIONS
from hydrodataset.camels import Camels, time_intersect_dynamic_data

CAMELS_NO_DATASET_ERROR_LOG = (
    "We cannot read this dataset now. Please check if you choose correctly:\n"
    + str(CAMELS_REGIONS)
)

camelsdk_arg = {
    "forcing_type": "observation",
    "gauge_id_tag": "catch_id",
    "area_tag": ["catch_area", ],
    "meanprcp_unit_tag": [["p_mean"], "mm/d"],
    "time_range": {
        "observation": ["1989-01-02", "2024-01-02"],
    },
    "target_cols": ["Qobs","Qdkm"],  # Qdkm means Qsim
    "b_nestedness": False,
    "forcing_unit": ["mm/d", "°C", "mm/d", "m", "mm/d", "-", "m^3/s", "m^3/s", "m", "m^3/s", "m^3/s"],
    "data_file_attr": {
        "sep": ",",
        "header": 0,
        "attr_file_str": ["CAMELS_DK_", ".csv", ]
    },
}

class CamelsDk(Camels):
    def __init__(
        self,
        data_path = os.path.join("camels","camels_dk"),
        download = False,
        region: str = "DK",
        arg: dict = camelsdk_arg,
    ):
        """
        Initialization for CAMELS-DK dataset

        Parameters
        ----------
        data_path
            where we put the dataset.
            we already set the ROOT directory for hydrodataset,
            so here just set it as a relative path,
            by default "camels/camels_dk"
        download
            if true, download, by default False
        region
            the default is CAMELS-DK
        """
        super().__init__(data_path, download, region, arg)

    def _set_data_source_camels_describe(self, camels_db):
        # shp file of basins
        camels_shp_file = camels_db.joinpath(
            "Shapefile",
            "CAMELS_DK_304_gauging_catchment_boundaries.shp",
        )
        # flow and forcing data are in a same file
        flow_dir1 = camels_db.joinpath(
            "Dynamics",
            "Gauged_catchments",
        )
        flow_dir2 = camels_db.joinpath(
            "Dynamics",
            "Ungauged_catchments",
        )
        flow_dir = [flow_dir1, flow_dir2]
        # flow_dir = camels_db.joinpath(
        #         "Dynamics",
        #         "Gauged_catchments",
        #     )
        forcing_dir = flow_dir
        # attr
        attr_dir = camels_db.joinpath(
            "Attributes",
        )
        attr_key_lst = [
            "climate",
            "geology",
            "landuse",
            "signature_obs_based",
            "soil",
            "topography",
        ]
        gauge_id_file = attr_dir.joinpath("CAMELS_DK_climate.csv")
        # gauge_id_file = forcing_dir
        nestedness_information_file = None
        base_url = "https://gdex.ucar.edu/dataset/camels"
        download_url_lst = [
            f"{base_url}/file/basin_set_full_res.zip",
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
        all readable attrs in CAMELS-DK

        Returns
        -------
        np.ndarray
            attribute types
        """
        data_folder = self.data_source_description["CAMELS_ATTR_DIR"]
        return self._get_constant_cols_some(
            data_folder, "CAMELS_DK_",".csv",","
        )

    def get_relevant_cols(self) -> np.ndarray:
        """
        all readable forcing types in CAMELS-DK

        Returns
        -------
        np.ndarray
            forcing types
        """
        return np.array(
            [
                "precipitation",
                "temperature",
                "pet",
                "DKM_dtp",
                "DKM_eta",
                "DKM_wcr",
                "DKM_sdr",
                "DKM_sre",
                "DKM_gwh",
                "DKM_irr",
                "Abstraction",
            ]
        )

    def read_dk_gage_flow_forcing(self, gage_id, t_range, var_type):
        """
        Read gage's streamflow or forcing from CAMELS-DK

        Parameters
        ----------
        gage_id
            the station id
        t_range
            the time range, for example, ["1989-01-02", "2024-01-02"]
        var_type
            flow type: "Qobs","Qdkm"   # Qdkm means Qsim
            forcing type: "precipitation","temperature","pet","DKM_dtp","DKM_eta","DKM_wcr","DKM_sdr","DKM_sre","DKM_gwh","DKM_irr","Abstraction"

        Returns
        -------
        np.array
            streamflow or forcing data of one station for a given time range
        """
        logging.debug("reading %s streamflow data", gage_id)
        # locate the gage file
        gage_file1 = os.path.join(
            self.data_source_description["CAMELS_FLOW_DIR"][0],
            "CAMELS_DK_obs_based_" + gage_id + ".csv",
        )
        gage_file2 = os.path.join(
            self.data_source_description["CAMELS_FLOW_DIR"][1],
            "CAMELS_DK_sim_based_" + gage_id + ".csv",
        )
        if os.path.exists(gage_file1):
            gage_file = gage_file1
        elif os.path.exists(gage_file2):
            gage_file = gage_file2
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"])

        obs = data_temp[var_type].values
        if var_type in self.target_cols:
            obs[obs < 0] = np.nan
        date = pd.to_datetime(data_temp["time"]).values.astype("datetime64[D]")
        return time_intersect_dynamic_data(obs, date, t_range)

    def read_target_cols(
        self,
        gage_id_lst: Union[list, np.array] = None,
        t_range: list = None,
        target_cols: Union[list, np.array] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        read target values. for CAMELS-DK, they are streamflows.

        default target_cols is an one-value list
        Notice, the unit of target outputs in different regions are not totally same

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1989-01-02", "2024-01-02"]
        target_cols
            the default is None, but we need at least one default target.
            For CAMELS-DK, it's ["Qobs","Qdkm"]
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
            range(len(target_cols)), desc="Read streamflow data of CAMELS-DK"
        ):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_dk_gage_flow_forcing(
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
        forcing_type="observation",
        **kwargs,
    ) -> np.ndarray:
        """
        Read forcing data

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1989-01-02", "2024-01-02"]
        var_lst
            forcing variable type: "precipitation","temperature","pet","DKM_dtp","DKM_eta","DKM_wcr","DKM_sdr","DKM_sre","DKM_gwh","DKM_irr","Abstraction"
        forcing_type
            support for CAMELS-DK, there are ** types:
        Returns
        -------
        np.array
            forcing data
        """
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        x = np.full([len(gage_id_lst), nt, len(var_lst)], np.nan)
        for j in tqdm(range(len(var_lst)), desc="Read forcing data of CAMELS-DK"):
            for k in tqdm(range(len(gage_id_lst))):
                data_forcing = self.read_dk_gage_flow_forcing(
                    gage_id_lst[k], t_range, var_lst[j]
                )
                x[k, :, j] = data_forcing
        return x

    def get_attribute_units_dict(self):
        """

        Returns
        -------

        """
        units_dict = {
            "p_mean": "mm/day",
            "t_mean": "Celsius degree",
            "pet_mean": "mm/day",
            "aridity": "dimensionless",
            "high_prec_freq": "day/year",
            "high_prec_dur": "d",
            "high_prec_timing": "season",
            "low_prec_freq": "day/year",
            "low_prec_dur": "d",
            "low_prec_timing": "season",
            "frac_snow_daily": "percent",
            "p_seasonality": "dimensionless",
            "pct_aeolain_sand": "percent",
            "pct_water_deposit": "percent",
            "pct_marsh": "percent",
            "pct_marine_sand": "percent",
            "pct_beach": "percent",
            "pct_sandy_till": "percent",
            "pct_till": "percent",
            "pct_glaf_sand": "percent",
            "pct_glal_clay": "percent",
            "pct_down_sand": "percent",
            "pct_glam_clay": "percent",
            "chalk_d": "m",
            "uaquifer_t": "m",
            "uaquifer_d": "m",
            "uclay_t": "m",
            "usand_t": "m",
            "pct_forest_levin_2011": "percent",
            "pct_agriculture_levin_2011": "percent",
            "pct_water_levin_2011": "percent",
            "pct_urban_levin_2011": "percent",
            "pct_naturedry_levin_2011": "percent",
            "pct_naturewet_levin_2011": "percent",
            "pct_forest_levin_2016": "percent",
            "pct_agriculture_levin_2016": "percent ",
            "pct_water_levin_2016": "percent",
            "pct_urban_levin_2016": "percent",
            "pct_naturedry_levin_2016": "percent",
            "pct_naturewet_levin_2016": "percent",
            "pct_forest_levin_2018": "percent",
            "pct_agriculture_levin_2018": "percent",
            "pct_water_levin_2018": "percent",
            "pct_urban_levin_2018": "percent",
            "pct_naturedry_levin_2018": "percent",
            "pct_naturewet_levin_2018": "percent",
            "pct_forest_levin_2021": "percent ",
            "pct_agriculture_levin_2021": "percent",
            "pct_water_levin_2021": "percent",
            "pct_urban_levin_2021": "percent",
            "pct_naturedry_levin_2021": "percent",
            "pct_naturewet_levin_2021": "percent",
            "pct_forest_corine_1990": "percent",
            "pct_agriculture_corine_1990": "percent",
            "pct_water_corine_1990": "percent",
            "pct_urban_corine_1990": "percent",
            "pct_wetlands_corine_1990": "percent",
            "pct_forest_corine_2000": "percent ",
            "pct_agriculture_corine_2000": "percent",
            "pct_water_corine_2000": "percent",
            "pct_urban_corine_2000": "percent",
            "pct_wetlands_corine_2000": "percent",
            "pct_forest_corine_2006": "percent",
            "pct_agriculture_corine_2006": "percent",
            "pct_water_corine_2006": "percent",
            "pct_urban_corine_2006": "percent",
            "pct_wetlands_corine_2006": "percent",
            "pct_forest_corine_2012": "percent",
            "pct_agriculture_corine_2012": "percent ",
            "pct_water_corine_2012": "percent",
            "pct_urban_corine_2012": "percent",
            "pct_wetlands_corine_2012": "percent",
            "pct_forest_corine_2018": "percent",
            "pct_agriculture_corine_2018": "percent",
            "pct_water_corine_2018": "percent",
            "pct_urban_corine_2018": "percent",
            "pct_wetlands_corine_2018": "percent",
            "Q_mean": "mm/day",
            "Q5": "mm/timestep",
            "Q95": "mm/timestep",
            "Q_7_day_min": "mm/day",
            "BFI": "percent",
            "CoV": "dimensionless",
            "high_Q_frequency": "dimensionless",
            "low_Q_frequency": "dimensionless",
            "zero_Q_frequency": "dimensionless",
            "high_Q_duration": "timestep",
            "low_Q_duration": "timestep",
            "zero_Q_duration": "day",
            "HFD_mean": "day/year",
            "HFI_mean": "day",
            "AC1": "dimensionless",
            "FDC_slope": "percent",
            "BaseflowRecessionK": "1/d",
            "TotalRR": "percent",
            "QP_elasticity": "percent",
            "SnowDayRatio": "dimensionless",
            "RLD": "1/day",
            "RR_Seasonality": "dimensionless",
            "EventRR": "dimensionless",
            "StorageFraction": "dimensionless",
            "Recession_a_Seasonality": "dimensionless",
            "AverageStorage": "dimensionless",
            "Spearmans_rho": "dimensionless",
            "EventRR_TotalRR_ratio": "dimensionless",
            "VariabilityIndex": "dimensionless",
            "IE_effect": "dimensionless",
            "SE_effect": "dimensionless",
            "IE_thresh_signif": "dimensionless",
            "IE_thresh": "mm/day",
            "SE_thresh_signif": "dimensionless",
            "SE_thresh": "mm",
            "SE_slope": "dimensionless",
            "Storage_thresh_signif": "dimensionless",
            "Storage_thresh": "mm",
            "min_Qf_perc": "percent",
            "BaseflowMagnitude": "mm",
            "ResponseTime": "day",
            "FlashinessIndex": "dimensionless",
            "PQ_Curve": "dimensionless",
            "Q_n_day_max": "mm/day",
            "Q_skew": "mm^3/day^3",
            "Q_var": "mm^2/day^2",
            "RecessionK_part": "1/day",
            "SeasonalTranslation": "dimensionless",
            "SnowStorage": "mm",
            "root_depth": "m",
            "pct_sand": "percent",
            "pct_silt": "percent",
            "pct_clay": "percent",
            "pct_organic": "percent",
            "pct_gravel": "percent",
            "tawc": "mm",
            "bulk_density": "g/cm^3",
            "pct_claynor_30": "percent",
            "pct_claynor_60": "percent",
            "pct_claynor_100": "percent",
            "pct_claynor_200": "percent",
            "pct_fsandno_30": "percent",
            "pct_fsandno_60": "percent",
            "pct_fsandno_100": "percent",
            "pct_fsandno_200": "percent",
            "pct_gsandno_30": "percent",
            "pct_gsandno_60": "percent",
            "pct_gsandno_100": "percent",
            "pct_gsandno_200": "percent",
            "FC": "cm^3/cm^3",
            "HCC": "log10[cm/day]",
            "KS": "log10[cm/day]",
            "MRC": "cm^3/cm^3",
            "THS": "cm^3/cm^3",
            "WP": "cm^3/cm^3",
            "catch_outlet_lon": "degree",
            "catch_outlet_lat": "degree",
            "catch_flow_dir": "dimensionless",
            "catch_accum_number": "dimensionless",
            "catch_area": "m^2",
            "gauged_type": "dimensionless",
            "gauge_record_pct": "percent",
            "dem_mean": "m",
            "dem_max": "m",
            "dem_median": "m",
            "dem_min": "m",
            "slope_mean": "m/km",
            "slope_median": "m/km",
            "slope_max": "m/km",
            "slope_min": "m/km",
            "pct_flat_area": "percent",
        }

        return units_dict
