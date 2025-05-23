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
from pandas.api.types import is_string_dtype, is_numeric_dtype

CAMELS_NO_DATASET_ERROR_LOG = (
    "We cannot read this dataset now. Please check if you choose correctly:\n"
    + str(CAMELS_REGIONS)
)

camelsfr_arg = {
    "forcing_type": "observation",
    "gauge_id_tag": "sta_code_h3",
    "area_tag": ["sta_area_snap", ],
    "meanprcp_unit_tag": [["cli_prec_mean"], "mm/d"],
    "time_range": {
        "observation": ["1970-01-01", "2022-01-01"],
    },
    "target_cols": ["tsd_q_l", "tsd_q_mm"],
    "b_nestedness": True,
    "forcing_unit": ["mm/day", "-", "°C", "mm/day", "mm/day", "mm/day", "m/s", "g/kg", "J/cm^2", "J/cm^2", "-", "-", "mm/day", "°C", "°C"],
    "data_file_attr": {
        "sep": ";",
        "header": 0,
        "attr_file_str": ["CAMELS_FR_", "_attributes.csv", ".csv"]
    },
}

class CamelsFr(Camels):
    def __init__(
        self,
        data_path = os.path.join("camels","camels_fr"),
        download = False,
        region: str = "FR",
        arg: dict = camelsfr_arg,
    ):
        """
        Initialization for CAMELS-FR dataset

        Parameters
        ----------
        data_path
            where we put the dataset.
            we already set the ROOT directory for hydrodataset,
            so here just set it as a relative path,
            by default "camels/camels_fr"
        download
            if true, download, by default False
        region
            the default is CAMELS-FR
        """
        super().__init__(data_path, download, region, arg)

    def _set_data_source_camels_describe(self, camels_db):
        # shp file of basins
        camels_shp_file = camels_db.joinpath(
            "CAMELS_FR_geography",
            "CAMELS_FR_catchment_boundaries.gpkg", # todo: fr gives a gis database file, maybe need a manually transform.
        )
        # flow and forcing data are in a same file
        flow_dir = camels_db.joinpath(
            "CAMELS_FR_time_series",
            "daily",
        )
        forcing_dir = flow_dir
        # attr
        attr_dir1 = camels_db.joinpath(
            "CAMELS_FR_attributes",
            "static_attributes",
        )
        attr_dir2 = camels_db.joinpath(
            "CAMELS_FR_attributes",
            "time_series_statistics"
        )
        attr_dir = [attr_dir1, attr_dir2]
        attr_key_lst = [    # the commented attribution files have different number of rows with station number
            "geology",
            "human_influences_dams",
            "hydrogeology",
            "land_cover",
            # "site_general",   # metadata   "sit_area_hydro", hydrological catchment area
            # "soil_general",
            # "soil_quantiles",
            "station_general",  # metadata   "sta_area_snap"  topographic catchment area (INRAE's own computation)
            "topography_general",
            # "topography_quantiles",
            "climatic_statistics",      # time_series_statistics
            # "hydroclimatic_quantiles",
            # "hydroclimatic_regimes_daily",
            "hydroclimatic_statistics_joint_availability_yearly",
            # "hydroclimatic_statistics_timeseries_yearly",
            "hydrological_signatures",
            "hydrometry_statistics",
        ]
        gauge_id_file = attr_dir1.joinpath("CAMELS_FR_geology_attributes.csv")
        nestedness_information_file = camels_db.joinpath(
            "CAMELS_FR_geography",
            "CAMELS_FR_catchment_nestedness_information.csv",
        )
        base_url = "https://entrepot.recherche.data.gouv.fr"
        download_url_lst = [
            f"{base_url}/api/access/datafiles?gbrecs=true&format=original",
        ]

        return collections.OrderedDict(
            CAMELS_DIR = camels_db,
            CAMELS_FLOW_DIR = flow_dir,
            CAMELS_FORCING_DIR = forcing_dir,
            CAMELS_ATTR_DIR = attr_dir,
            CAMELS_ATTR_KEY_LST = attr_key_lst,
            CAMELS_GAUGE_FILE = gauge_id_file,
            CAMELS_NESTEDNESS_FILE = nestedness_information_file,
            CAMELS_BASINS_SHP = camels_shp_file,
            CAMELS_DOWNLOAD_URL_LST=download_url_lst,
        )

    def get_constant_cols(self) -> np.ndarray:
        """
        all readable attrs in CAMELS-FR

        Returns
        -------
        np.ndarray
            attribute types
        """
        data_folder = self.data_source_description["CAMELS_ATTR_DIR"]
        return self._get_constant_cols_some(
            data_folder, "CAMELS_FR_","_attributes.csv",";"
        )

    def get_relevant_cols(self) -> np.ndarray:
        """
        all readable forcing types in CAMELS-FR

        Returns
        -------
        np.ndarray
            forcing types
        """
        return np.array(
            [
                "tsd_prec",
                "tsd_prec_solid_frac",
                "tsd_temp",
                "tsd_pet_ou",
                "tsd_pet_pe",
                "tsd_pet_pm",
                "tsd_wind",
                "tsd_humid",
                "tsd_rad_dli",
                "tsd_rad_ssi",
                "tsd_swi_gr",
                "tsd_swi_isba",
                "tsd_swe_isba",
                "tsd_temp_min",
                "tsd_temp_max",
            ]
        )

    def read_fr_gage_flow_forcing(self, gage_id, t_range, var_type):
        """
        Read gage's streamflow or forcing from CAMELS-FR

        Parameters
        ----------
        gage_id
            the station id
        t_range
            the time range, for example, ["1970-01-01", "2022-01-01"]
        var_type
            flow type: "tsd_q_l", "tsd_q_mm"
            forcing type: "tsd_prec","tsd_prec_solid_frac","tsd_temp","tsd_pet_ou","tsd_pet_pe","tsd_pet_pm","tsd_wind",
            "tsd_humid","tsd_rad_dli","tsd_rad_ssi","tsd_swi_gr","tsd_swi_isba","tsd_swe_isba","tsd_temp_min","tsd_temp_max"

        Returns
        -------
        np.array
            streamflow or forcing data of one station for a given time range
        """
        logging.debug("reading %s streamflow data", gage_id)
        gage_file = os.path.join(
            self.data_source_description["CAMELS_FLOW_DIR"],
            "CAMELS_FR_tsd_" + gage_id + ".csv",
        )
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"], header=7)  # no need the "skiprows"
        obs = data_temp[var_type].values
        # if var_type in self.target_cols:  # todo:
        #     obs[obs < 0] = np.nan
        date = pd.to_datetime(pd.Series(data_temp["tsd_date"]),format="%Y%m%d").dt.strftime("%Y-%m-%d").values.astype("datetime64[D]")
        return time_intersect_dynamic_data(obs, date, t_range)

    def read_target_cols(
        self,
        gage_id_lst: Union[list, np.array] = None,
        t_range: list = None,
        target_cols: Union[list, np.array] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        read target values. for CAMELS-FR, they are streamflows.

        default target_cols is an one-value list
        Notice, the unit of target outputs in different regions are not totally same

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1970-01-01", "2022-01-01"]
        target_cols
            the default is None, but we need at least one default target.
            For CAMELS-FR, it's ["tsd_q_l"]
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
            range(len(target_cols)), desc="Read streamflow data of CAMELS-FR"
        ):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_fr_gage_flow_forcing(
                    gage_id_lst[k], t_range, target_cols[j]
                )
                y[k, :, j] = data_obs
        # Keep unit of streamflow unified: we use ft3/s here
        # unit conversion  L/s -> ft3/s
        y = self.unit_convert_streamflow_Ltofoot3(y)
        return y

    def read_relevant_cols(
        self,
        gage_id_lst: list = None,
        t_range: list = None,
        var_lst: list = None,
        forcing_type="nan",
        **kwargs,
    ) -> np.ndarray:
        """
        Read forcing data

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1970-01-01", "2022-01-01"]
        var_lst
            forcing variable type: "tsd_prec","tsd_prec_solid_frac","tsd_temp","tsd_pet_ou","tsd_pet_pe","tsd_pet_pm","tsd_wind",
            "tsd_humid","tsd_rad_dli","tsd_rad_ssi","tsd_swi_gr","tsd_swi_isba","tsd_swe_isba","tsd_temp_min","tsd_temp_max"
        forcing_type
            support for CAMELS-FR, there are ** types:
        Returns
        -------
        np.array
            forcing data
        """
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        x = np.full([len(gage_id_lst), nt, len(var_lst)], np.nan)
        for j in tqdm(range(len(var_lst)), desc="Read forcing data of CAMELS-FR"):
            for k in tqdm(range(len(gage_id_lst))):
                data_forcing = self.read_fr_gage_flow_forcing(
                    gage_id_lst[k], t_range, var_lst[j]
                )
                x[k, :, j] = data_forcing
        return x

    def read_attr_all(
        self,
        gages_ids: Union[list, np.ndarray]
    ):
        """
         Read Attributes data

        Parameters
        ----------
        gages_ids : Union[list, np.ndarray]
            gages sites' ids

        """
        data_folder1 = self.data_source_description["CAMELS_ATTR_DIR"][0]
        data_folder2 = self.data_source_description["CAMELS_ATTR_DIR"][1]
        key_lst = self.data_source_description["CAMELS_ATTR_KEY_LST"]
        f_dict = {}
        var_dict = {}
        var_lst = []
        out_lst = []
        camels_str1 = self.data_file_attr["attr_file_str"][0]
        camels_str2 = self.data_file_attr["attr_file_str"][1]
        camels_str3 = self.data_file_attr["attr_file_str"][2]
        sep_ = self.data_file_attr["sep"]
        n_gage = len(gages_ids)
        for key in key_lst:
            # locate the attribute file
            data_file1 = os.path.join(data_folder1, camels_str1 + key + camels_str2)
            data_file2 = os.path.join(data_folder2, camels_str1 + key + camels_str3)
            if os.path.exists(data_file1):
                data_file = data_file1
            elif os.path.exists(data_file2):
                data_file = data_file2
            data_temp = pd.read_csv(data_file, sep=sep_)
            var_lst_temp = list(data_temp.columns[1:])
            var_dict[key] = var_lst_temp
            var_lst.extend(var_lst_temp)
            k = 0
            print(len(var_lst_temp))
            out_temp = np.full([n_gage, len(var_lst_temp)], np.nan)
            for field in var_lst_temp:
                if is_string_dtype(data_temp[field]):
                    value, ref = pd.factorize(data_temp[field], sort=True)
                    out_temp[:, k] = value
                    f_dict[field] = ref.tolist()
                elif is_numeric_dtype(data_temp[field]):
                    out_temp[:, k] = data_temp[field].values
                k = k + 1
            out_lst.append(out_temp)
        out = np.concatenate(out_lst, 1)
        return out, var_lst, var_dict, f_dict

    def get_attribute_units_dict(self):
        """

        Returns
        -------

        """
        units_dict = {
            "geo_dom_class": "dimensionless",
            "geo_su": "percent",
            "geo_ss": "percent",
            "geo_py": "percent",
            "geo_sm": "percent",
            "geo_sc": "percent",
            "geo_ev": "percent",
            "geo_va": "percent",
            "geo_vi": "percent",
            "geo_vb": "percent",
            "geo_pa": "percent",
            "geo_pi": "percent",
            "geo_pb": "percent",
            "geo_mt": "percent",
            "geo_wb": "percent",
            "geo_ig": "percent",
            "geo_nd": "percent",
            "dam_n": "dimensionless",
            "dam_volume": "Mm^3",
            "dam_influence": "mm",
            "hgl_krs_not_karstic": "percent",
            "hgl_krs_karstic": "percent",
            "hgl_krs_unknown": "percent",
            "hgl_thm_alluvial": "percent",
            "hgl_thm_sedimentary": "percent",
            "hgl_thm_bedrock": "percent",
            "hgl_thm_intense_folded": "percent",
            "hgl_thm_volcanism": "percent",
            "hgl_thm_unknown": "percent",
            "hgl_permeability": "log10(m^2)",
            "hgl_porosity": "dimensionless",
            "clc_2018_lvl1_dom_class": "dimensionless",
            "clc_2018_lvl1_1": "percent",
            "clc_2018_lvl1_2": "percent",
            "clc_2018_lvl1_3": "percent",
            "clc_2018_lvl1_4": "percent",
            "clc_2018_lvl1_5": "percent",
            "clc_2018_lvl1_na": "percent",
            "clc_2018_lvl2_dom_class": "dimensionless",
            "clc_2018_lvl2_11": "percent",
            "clc_2018_lvl2_12": "percent",
            "clc_2018_lvl2_13": "percent",
            "clc_2018_lvl2_14": "percent",
            "clc_2018_lvl2_21": "percent",
            "clc_2018_lvl2_22": "percent",
            "clc_2018_lvl2_23": "percent",
            "clc_2018_lvl2_24": "percent",
            "clc_2018_lvl2_31": "percent",
            "clc_2018_lvl2_32": "percent",
            "clc_2018_lvl2_33": "percent",
            "clc_2018_lvl2_41": "percent",
            "clc_2018_lvl2_42": "percent",
            "clc_2018_lvl2_51": "percent",
            "clc_2018_lvl2_52": "percent",
            "clc_2018_lvl2_na": "percent",
            "clc_2018_lvl3_dom_class": "dimensionless",
            "clc_2018_lvl3_111": "percent",
            "clc_2018_lvl3_112": "percent",
            "clc_2018_lvl3_121": "percent",
            "clc_2018_lvl3_122": "percent",
            "clc_2018_lvl3_123": "percent",
            "clc_2018_lvl3_124": "percent",
            "clc_2018_lvl3_131": "percent",
            "clc_2018_lvl3_132": "percent",
            "clc_2018_lvl3_133": "percent",
            "clc_2018_lvl3_141": "percent",
            "clc_2018_lvl3_142": "percent",
            "clc_2018_lvl3_211": "percent",
            "clc_2018_lvl3_212": "percent",
            "clc_2018_lvl3_213": "percent",
            "clc_2018_lvl3_221": "percent",
            "clc_2018_lvl3_222": "percent",
            "clc_2018_lvl3_223": "percent",
            "clc_2018_lvl3_231": "percent",
            "clc_2018_lvl3_241": "percent",
            "clc_2018_lvl3_242": "percent",
            "clc_2018_lvl3_243": "percent",
            "clc_2018_lvl3_244": "percent",
            "clc_2018_lvl3_311": "percent",
            "clc_2018_lvl3_312": "percent",
            "clc_2018_lvl3_313": "percent",
            "clc_2018_lvl3_321": "percent",
            "clc_2018_lvl3_322": "percent",
            "clc_2018_lvl3_323": "percent",
            "clc_2018_lvl3_324": "percent",
            "clc_2018_lvl3_331": "percent",
            "clc_2018_lvl3_332": "percent",
            "clc_2018_lvl3_333": "percent",
            "clc_2018_lvl3_334": "percent",
            "clc_2018_lvl3_335": "percent",
            "clc_2018_lvl3_411": "percent",
            "clc_2018_lvl3_412": "percent",
            "clc_2018_lvl3_421": "percent",
            "clc_2018_lvl3_422": "percent",
            "clc_2018_lvl3_423": "percent",
            "clc_2018_lvl3_511": "percent",
            "clc_2018_lvl3_512": "percent",
            "clc_2018_lvl3_521": "percent",
            "clc_2018_lvl3_522": "percent",
            "clc_2018_lvl3_523": "percent",
            "clc_2018_lvl3_na": "percent",
            "clc_1990_lvl1_dom_class": "dimensionless",
            "clc_1990_lvl1_1": "percent",
            "clc_1990_lvl1_2": "percent",
            "clc_1990_lvl1_3": "percent",
            "clc_1990_lvl1_4": "percent",
            "clc_1990_lvl1_5": "percent",
            "clc_1990_lvl1_na": "percent",
            "clc_1990_lvl2_dom_class": "dimensionless",
            "clc_1990_lvl2_11": "percent",
            "clc_1990_lvl2_12": "percent",
            "clc_1990_lvl2_13": "percent",
            "clc_1990_lvl2_14": "percent",
            "clc_1990_lvl2_21": "percent",
            "clc_1990_lvl2_22": "percent",
            "clc_1990_lvl2_23": "percent",
            "clc_1990_lvl2_24": "percent",
            "clc_1990_lvl2_31": "percent",
            "clc_1990_lvl2_32": "percent",
            "clc_1990_lvl2_33": "percent",
            "clc_1990_lvl2_41": "percent",
            "clc_1990_lvl2_42": "percent",
            "clc_1990_lvl2_51": "percent",
            "clc_1990_lvl2_52": "percent",
            "clc_1990_lvl2_na": "percent",
            "clc_1990_lvl3_dom_class": "dimensionless",
            "clc_1990_lvl3_111": "percent",
            "clc_1990_lvl3_112": "percent",
            "clc_1990_lvl3_121": "percent",
            "clc_1990_lvl3_122": "percent",
            "clc_1990_lvl3_123": "percent",
            "clc_1990_lvl3_124": "percent",
            "clc_1990_lvl3_131": "percent",
            "clc_1990_lvl3_132": "percent",
            "clc_1990_lvl3_133": "percent",
            "clc_1990_lvl3_141": "percent",
            "clc_1990_lvl3_142": "percent",
            "clc_1990_lvl3_211": "percent",
            "clc_1990_lvl3_212": "percent",
            "clc_1990_lvl3_213": "percent",
            "clc_1990_lvl3_221": "percent",
            "clc_1990_lvl3_222": "percent",
            "clc_1990_lvl3_223": "percent",
            "clc_1990_lvl3_231": "percent",
            "clc_1990_lvl3_241": "percent",
            "clc_1990_lvl3_242": "percent",
            "clc_1990_lvl3_243": "percent",
            "clc_1990_lvl3_244": "percent",
            "clc_1990_lvl3_311": "percent",
            "clc_1990_lvl3_312": "percent",
            "clc_1990_lvl3_313": "percent",
            "clc_1990_lvl3_321": "percent",
            "clc_1990_lvl3_322": "percent",
            "clc_1990_lvl3_323": "percent",
            "clc_1990_lvl3_324": "percent",
            "clc_1990_lvl3_331": "percent",
            "clc_1990_lvl3_332": "percent",
            "clc_1990_lvl3_333": "percent",
            "clc_1990_lvl3_334": "percent",
            "clc_1990_lvl3_335": "percent",
            "clc_1990_lvl3_411": "percent",
            "clc_1990_lvl3_412": "percent",
            "clc_1990_lvl3_421": "percent",
            "clc_1990_lvl3_422": "percent",
            "clc_1990_lvl3_423": "percent",
            "clc_1990_lvl3_511": "percent",
            "clc_1990_lvl3_512": "percent",
            "clc_1990_lvl3_521": "percent",
            "clc_1990_lvl3_522": "percent",
            "clc_1990_lvl3_523": "percent",
            "clc_1990_lvl3_na": "percent",
            "top_altitude_mean": "m.a.s.l.",
            "top_slo_mean": "degree",
            "top_dist_outlet_mean": "km",
            "top_itopo_mean": "dimensionless",
            "top_slo_ori_n": "percent",
            "top_slo_ori_ne": "percent",
            "top_slo_ori_e": "percent",
            "top_slo_ori_se": "percent",
            "top_slo_ori_s": "percent",
            "top_slo_ori_sw": "percent",
            "top_slo_ori_w": "percent",
            "top_slo_ori_nw": "percent",
            "top_drainage_density": "km/km^2",
            "top_mor_form_factor_horton": "dimensionless",
            "top_mor_form_factor_square": "dimensionless",
            "top_mor_shape_factor": "dimensionless",
            "top_mor_compact_coef": "dimensionless",
            "top_mor_circ_ratio": "dimensionless",
            "top_mor_elong_ratio_circ": "dimensionless",
            "top_mor_elong_ratio_catchment": "dimensionless",
            "top_mor_relief_ratio": "dimensionless",
            "top_slo_flat": "percent",
            "top_slo_gentle": "percent",
            "top_slo_moderate": "percent",
            "top_slo_strong": "percent",
            "top_slo_steep": "percent",
            "top_slo_very_steep": "percent",
            "cli_prec_mean": "mm/day",
            "cli_pet_ou_mean": "mm/day",
            "cli_pet_pe_mean": "mm/day",
            "cli_pet_pm_mean": "mm/day",
            "cli_prec_mean_yr": "mm/yr",
            "cli_pet_ou_yr": "mm/yr",
            "cli_pet_pe_yr": "mm/yr",
            "cli_pet_pm_yr": "mm/yr",
            "cli_temp_mean": "°C/day",
            "cli_psol_frac_safran": "dimensionless",
            "cli_psol_frac_berghuijs": "dimensionless",
            "cli_aridity_ou": "dimensionless",
            "cli_aridity_pe": "dimensionless",
            "cli_aridity_pm": "dimensionless",
            "cli_prec_season_temp": "dimensionless",
            "cli_prec_season_pet_ou": "dimensionless",
            "cli_prec_season_pet_pe": "dimensionless",
            "cli_prec_season_pet_pm": "dimensionless",
            "cli_assync_ou": "dimensionless",
            "cli_assync_pe": "dimensionless",
            "cli_assync_pm": "dimensionless",
            "cli_prec_intensity": "dimensionless",
            "cli_prec_max": "mm/day",
            "cli_prec_date_max": "dimensionless",
            "cli_prec_freq_high": "days/yr",
            "cli_prec_dur_high": "days",
            "cli_prec_timing_high": "season",
            "cli_prec_freq_low": "days/yr",
            "cli_prec_dur_low": "days",
            "cli_prec_timing_low": "season",
            "hcy_qnt_quant": "dimensionless",
            "hcy_qnt_q": "mm/day",
            "hcy_qnt_prec": "mm/day",
            "hcy_qnt_temp": "°C/day",
            "hcy_qnt_pet_ou": "mm/day",
            "hcy_qnt_pet_pe": "mm/day",
            "hcy_qnt_pet_pm": "mm/day",
            "hcy_reg_quant": "dimensionless",
            "hcy_reg_day": "dimensionless",
            "hcy_reg_q": "mm/day",
            "hcy_reg_prec": "mm/day",
            "hcy_reg_temp": "°C/day",
            "hcy_reg_pet_ou": "mm/day",
            "hcy_reg_pet_pe": "mm/day",
            "hcy_reg_pet_pm": "mm/day",
            "hyc_jay_prec_mean": "mm/yr",
            "hyc_jay_pet_ou": "mm/yr",
            "hyc_jay_pet_pe": "mm/yr",
            "hyc_jay_pet_pm": "mm/yr",
            "hyc_jay_ratio_prec_pet_ou": "dimensionless",
            "hyc_jay_ratio_prec_pet_pe": "dimensionless",
            "hyc_jay_ratio_prec_pet_pm": "dimensionless",
            "hyc_jay_ratio_q_prec": "dimensionless",
            "hcy_tsy_year": "yr",
            "hcy_tsy_q_qmna": "mm/month",
            "hcy_tsy_q_max_day": "mm/day",
            "hcy_tsy_prec_daily_max": "mm/day",
            "hcy_tsy_prec_season_pet_ou": "dimensionless",
            "hcy_tsy_prec_season_pet_pe": "dimensionless",
            "hcy_tsy_prec_season_pet_pm": "dimensionless",
            "hyd_q_mean": "mm/day",
            "hyd_q_mean_yr": "mm/yr",
            "hyd_stream_elas": "dimensionless",
            "hyd_slope_fdc": "dimensionless",
            "hyd_bfi_ladson": "dimensionless",
            "hyd_bfi_lfstat": "dimensionless",
            "hyd_bfi_pelletier_pet_ou": "dimensionless",
            "hyd_hfd_mean": "days",
            "hyd_q_freq_high": "days/yr",
            "hyd_q_dur_high": "days",
            "hyd_q_freq_low": "days/yr",
            "hyd_q_dur_low": "days",
            "hyd_q_freq_zero": "days/yr",
            "hyd_q_max": "mm/day",
            "hyd_q_date_max": "dimensionless",
            "hyd_q_qmna_min": "mm/month",
            "hyd_q_date_qmna": "dimensionless",
            "hym_q_date_start": "dimensionless",
            "hym_q_date_end": "dimensionless",
            "hym_q_na_period": "percent",
            "hym_q_na_total": "percent",
            "hym_q_n_year": "dimensionless",
            "hym_q_questionable": "percent",
            "hym_q_unqualified": "percent",
            "hym_q_anomaly_inrae": "percent",
            "hym_q_low_uncertainty_inrae": "dimensionless",
            # "sit_label": "dimensionless",       # "site_general"
            # "sit_mnemonic": "dimensionless",
            # "sit_label_usual": "dimensionless",
            # "sit_label_add": "dimensionless",
            # "sit_type": "dimensionless",
            # "sit_type_add": "dimensionless",
            # "sta_code_h2": "dimensionless",
            # "sit_test_site": "dimensionless",
            # "sit_comment": "dimensionless",
            # "sit_city": "dimensionless",
            # "sit_latitude": "°N or m",  # degree N
            # "sit_longitude": "°E or m",
            # "sit_crs": "dimensionless",
            # "sit_zone_hydro": "dimensionless",
            # "sit_section": "dimensionless",
            # "sit_entity": "dimensionless",
            # "sit_waterbody": "dimensionless",
            # "sit_watercourse_acc": "dimensionless",
            # "sit_altitude": "m.a.s.l.",
            # "sit_altitude_datum": "dimensionless",
            # "sit_area_hydro": "km^2",
            # "sit_area_topo": "km^2",
            # "sit_tz": "dimensionless",
            # "sit_kp_up": "m",
            # "sit_kp_down": "m",
            # "sit_flood_duration": "dimensionless",
            # "sit_status": "dimensionless",
            # "sit_publication_rights": "dimensionless",
            # "sit_month1_low_water": "dimensionless",
            # "sit_month1_year": "dimensionless",
            # "sit_impact": "dimensionless",
            # "sit_section_vigilance": "dimensionless",
            # "sit_date_start": "dimensionless",
            # "sit_comment_impact_gene": "dimensionless",
            # "sit_date_update": "dimensionless",
            "sta_label": "dimensionless",
            "sta_label_add": "dimensionless",
            "sta_type": "dimensionless",
            "sta_test_station": "dimensionless",
            "sta_monitor": "dimensionless",
            "sta_code_h2": "dimensionless",
            "sta_code_child": "dimensionless",
            "sta_code_parent": "dimensionless",
            "sta_comment": "dimensionless",
            "sta_city": "dimensionless",
            "sta_crs": "dimensionless",
            "sta_epsg": "dimensionless",
            "sta_kp": "m",
            "sta_altitude_staff_gauge": "mm",
            "sta_date_altitude_ref": "dimensionless",
            "sta_date_start": "dimensionless",
            "sta_date_end": "dimensionless",
            "sta_publication_right": "dimensionless",
            "sta_time_data_gap": "min",
            "sta_time_discontinuity": "min",
            "sta_impact_local": "dimensionless",
            "sta_display_level": "dimensionless",
            "sta_dual_staff_gauge": "dimensionless",
            "sta_qual_lowflow": "dimensionless",
            "sta_qual_meanflow": "dimensionless",
            "sta_qual_highflow": "dimensionless",
            "sta_purpose": "dimensionless",
            "sta_comment_impact_local": "dimensionless",
            "sta_date_update": "dimensionless",
            "sit_code_h3": "dimensionless",
            "sta_main_prod_name": "dimensionless",
            "sta_main_prod_name_short": "dimensionless",
            "sta_main_prod_code": "dimensionless",
            "sta_x_l2e": "m",
            "sta_y_l2e": "m",
            "sta_x_l93": "m",
            "sta_y_l93": "m",
            "sta_x_w84": "degree E",
            "sta_y_w84": "degree N",
            "sta_x_l2e_snap": "m",
            "sta_y_l2e_snap": "m",
            "sta_x_l93_snap": "m",
            "sta_y_l93_snap": "m",
            "sta_x_w84_snap": "degree E",
            "sta_y_w84_snap": "degree N",
            "sta_area_snap": "km^2",
            "sta_altitude_snap": "m.a.s.l.",
            "sta_territory": "dimensionless",
        }

        return units_dict

    def cache_nestedness_df(self):
        """Save basin nestedness information data
        sta_code_h3: station code
        nes_is_nested: flag indicating whether the catchment is nested or not
        nes_n_station_ds: number of stations downstream
        nes_next_station_ds: sta_code_h3 of the closest downstream station
        nes_n_nested_within: number of sub-catchments within the catchment
        nes_dist_ds: hydraulic distance (theoretical horizontal stream length) from the actual stream-gauge station to the next downstream station
        nes_station_nested_within: sta_code_h3 of all sub-catchments within this catchment
        """
        nestedness_file = self.data_source_description["CAMELS_NESTEDNESS_FILE"]
        data_temp = pd.read_csv(nestedness_file, sep=";")
        data_temp.set_index(self.gauge_id_tag, inplace=True)
        data_temp.index.name = "basin"
        return data_temp

    def read_nestedness_csv(self,**kwargs):
        filename = "camels" + self.region.lower()
        filename = filename + "_nestedness.csv"
        camels_ntcsv = CACHE_DIR.joinpath(filename)
        if (not os.path.isfile(camels_ntcsv)) and self.b_nestedness:
            self.cache_xrdataset()
        nt = pd.read_csv(camels_ntcsv, sep=";")
        nt.set_index("basin", inplace=True)
        return nt
