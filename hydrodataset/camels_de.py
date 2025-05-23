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

camelsde_arg = {
    "forcing_type": "observation",
    "gauge_id_tag": "gauge_id",
    "area_tag": ["area", ],
    "meanprcp_unit_tag": [["p_mean"], "mm/d"],
    "time_range": {
        "observation": ["1951-01-01", "2021-01-01"],
    },
    "target_cols": ["discharge_vol", "discharge_spec"],
    "b_nestedness": False,
    "forcing_unit": ["m", "mm/d", "mm/d", "mm/d", "mm/d", "mm/d", "%", "%", "%", "%", "%", "W/m^2", "W/m^2", "W/m^2",
                     "W/m^2", "W/m^2", "°C", "°C", "°C"],
    "data_file_attr": {
        "sep": ",",
        "header": 0,
        "attr_file_str": ["CAMELS_DE_", "_attributes.csv",],
    },
}

class CamelsDe(Camels):
    def __init__(
        self,
        data_path = os.path.join("camels","camels_de"),
        download = False,
        region: str = "DE",
        arg: dict = camelsde_arg,
    ):
        """
        Initialization for CAMELS-DE dataset

        Parameters
        ----------
        data_path
            where we put the dataset.
            we already set the ROOT directory for hydrodataset,
            so here just set it as a relative path,
            by default "camels/camels_de"
        download
            if true, download, by default False
        region
            the default is CAMELS-DE
        """
        super().__init__(data_path, download, region, arg)

    def _set_data_source_camels_describe(self, camels_db):
        # shp file of basins
        camels_shp_file = camels_db.joinpath(
            "CAMELS_DE_catchment_boundaries",
            "catchments",
            "CAMELS_DE_catchments.shp",
        )
        # flow and forcing data are in a same file
        flow_dir = camels_db.joinpath(
            "timeseries",
        )
        forcing_dir = flow_dir
        # attr
        attr_dir = camels_db.joinpath()
        attr_key_lst = [
            "climatic",
            "humaninfluence",
            "hydrogeology",
            "hydrologic",
            "landcover",
            "soil",
            "topographic",
        ]
        gauge_id_file = attr_dir.joinpath("CAMELS_DE_hydrologic_attributes.csv")
        nestedness_information_file = None
        base_url = "https://zenodo.org/records/13837553"
        download_url_lst = [
            f"{base_url}/files/camels_de.zip",
            f"{base_url}/files/CAMELS_DE_Data_Description.pdf",
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
        all readable attrs in CAMELS-DE

        Returns
        -------
        np.ndarray
            attribute types
        """
        data_folder = self.data_source_description["CAMELS_ATTR_DIR"]
        return self._get_constant_cols_some(
            data_folder, "CAMELS_DE_","_attributes.csv",","
        )

    def get_relevant_cols(self) -> np.ndarray:
        """
        all readable forcing types in CAMELS-DE

        Returns
        -------
        np.ndarray
            forcing types
        """
        return np.array(
            [
                "water_level",
                "precipitation_mean",
                "precipitation_min",
                "precipitation_median",
                "precipitation_max",
                "precipitation_stdev",
                "humidity_mean",
                "humidity_min",
                "humidity_median",
                "humidity_max",
                "humidity_stdev",
                "radiation_global_mean",
                "radiation_global_min",
                "radiation_global_median",
                "radiation_global_max",
                "radiation_global_stdev",
                "temperature_mean",
                "temperature_min",
                "temperature_max",
            ]
        )

    def read_de_gage_flow_forcing(self, gage_id, t_range, var_type):
        """
        Read gage's streamflow or forcing from CAMELS-DE

        Parameters
        ----------
        gage_id
            the station id
        t_range
            the time range, for example, ["1951-01-01", "2021-01-01"]
        var_type
            flow type: "discharge_vol", "discharge_spec"
            forcing type: "water_level", "precipitation_mean", "precipitation_min", "precipitation_median",
            " precipitation_max", "precipitation_stdev", "humidity_mean", "humidity_min", " humidity_median",
            "humidity_max", "humidity_stdev", "radiation_global_mean", " radiation_global_min", "radiation_global_median",
            "radiation_global_max", " radiation_global_stdev", " temperature_mean", " temperature_min", " temperature_max"

        Returns
        -------
        np.array
            streamflow or forcing data of one station for a given time range
        """
        logging.debug("reading %s streamflow data", gage_id)
        gage_file = os.path.join(
            self.data_source_description["CAMELS_FLOW_DIR"],
            "CAMELS_DE_hydromet_timeseries_" + gage_id + ".csv",
        )
        data_temp = pd.read_csv(gage_file, sep=self.data_file_attr["sep"])
        obs = data_temp[var_type].values
        if var_type in self.target_cols:
            obs[obs < 0] = np.nan
        date = pd.to_datetime(data_temp["date"]).values.astype("datetime64[D]")
        return time_intersect_dynamic_data(obs, date, t_range)

    def read_target_cols(
        self,
        gage_id_lst: Union[list, np.array] = None,
        t_range: list = None,
        target_cols: Union[list, np.array] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        read target values. for CAMELS-DE, they are streamflows.

        default target_cols is an one-value list
        Notice, the unit of target outputs in different regions are not totally same

        Parameters
        ----------
        gage_id_lst
            station ids
        t_range
            the time range, for example, ["1951-01-01", "2021-01-01"]
        target_cols
            the default is None, but we need at least one default target.
            For CAMELS-DE, it's ["discharge_vol"]
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
            range(len(target_cols)), desc="Read streamflow data of CAMELS-DE"
        ):
            for k in tqdm(range(len(gage_id_lst))):
                data_obs = self.read_de_gage_flow_forcing(
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
            the time range, for example, ["1951-01-01", "2021-01-01"]
        var_lst
            forcing variable type: "water_level", "precipitation_mean", "precipitation_min", "precipitation_median",
            "precipitation_max", "precipitation_stdev", "humidity_mean", "humidity_min", "humidity_median",
            "humidity_max", "humidity_stdev", "radiation_global_mean", " radiation_global_min", "radiation_global_median",
            "radiation_global_max", "radiation_global_stdev", "temperature_mean", "temperature_min", "temperature_max"
        forcing_type
            support for CAMELS-DE, there are two types: c, simulated
        Returns
        -------
        np.array
            forcing data
        """
        t_range_list = hydro_time.t_range_days(t_range)
        nt = t_range_list.shape[0]
        x = np.full([len(gage_id_lst), nt, len(var_lst)], np.nan)
        for j in tqdm(range(len(var_lst)), desc="Read forcing data of CAMELS-DE"):
            for k in tqdm(range(len(gage_id_lst))):
                data_forcing = self.read_de_gage_flow_forcing(
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
            "p_mean": "mm/d",
            "p_seasonality": "dimensionless",
            "frac_snow": "dimensionless",
            "high_prec_freq": "d/yr",
            "high_prec_dur": "d",
            "high_prec_timing": "season",
            "low_prec_freq": "d/yr",
            "low_prec_dur": "d",
            "low_prec_timing": "season",
            "dams_names": "dimensionless",
            "dams_river_names": "dimensionless",
            "dams_num": "dimensionless",
            "dams_year_first": "dimensionless",
            "dams_year_last": "dimensionless",
            "dams_total_lake_area": "km^2",
            "dams_total_lake_volume": "Mio m^3",
            "dams_purposes": "dimensionless",
            "aquitard_perc": "percent",
            "aquifer_perc": "percent",
            "aquifer_aquitard_mixed_perc": "percent",
            "kf_very_high_perc": "percent",
            "kf_high_perc": "percent",
            "kf_medium_perc": "percent",
            "kf_moderate_perc": "percent",
            "kf_low_perc": "percent",
            "kf_very_low_perc": "percent",
            "kf_extremely_low_perc": "percent",
            "kf_very_high_to_high_perc": "percent",
            "kf_medium_to_moderate_perc": "percent",
            "kf_low_to_extremely_low_perc": "percent",
            "kf_highly_variable_perc": "percent",
            "kf_moderate_to_low_perc": "percent",
            "cavity_fissure_perc": "percent",
            "cavity_pores_perc": "percent",
            "cavity_fissure_karst_perc": "percent",
            "cavity_fissure_pores_perc": "percent",
            "rocktype_sediment_perc": "percent",
            "rocktype_metamorphite_perc": "percent",
            "rocktype_magmatite_perc": "percent",
            "consolidation_solid_rock_perc": "percent",
            "consolidation_unconsolidated_rock_perc": "percent",
            "geochemical_rocktype_silicate_perc": "percent",
            "geochemical_rocktype_silicate_carbonatic_perc": "percent",
            "geochemical_rocktype_carbonatic_perc": "percent",
            "geochemical_rocktype_sulfatic_perc": "percent",
            "geochemical_rocktype_silicate_organic_components_perc": "percent",
            "geochemical_rocktype_anthropogenically_modified_through_filling_perc": "percent",
            "geochemical_rocktype_sulfatic_halitic_perc": "percent",
            "geochemical_rocktype_halitic_perc": "percent",
            "waterbody_perc": "percent",
            "no_data_perc": "percent",
            "q_mean": "mm/d",
            "runoff_ratio": "dimensionless",
            "flow_period_start": "dimensionless",
            "flow_period_end": "dimensionless",
            "flow_perc_complete": "dimensionless",
            "slope_fdc": "dimensionless",
            "hfd_mean": "d",
            "Q5": "mm/d",
            "Q95": "mm/d",
            "high_q_freq": "d/yr",
            "high_q_dur": "d",
            "low_q_freq": "d/yr",
            "low_q_dur": "d",
            "zero_q_freq": "dimensionless",
            "artificial_surfaces_perc": "percent",
            "agricultural_areas_perc": "percent",
            "forests_and_seminatural_areas_perc": "percent",
            "wetlands_perc": "percent",
            "water_bodies_perc": "percent",
            "clay_0_30cm_mean": "g/100g (percent)",
            "clay_30_100cm_mean": "g/100g (percent)",
            "clay_100_200cm_mean": "g/100g (percent)",
            "silt_0_30cm_mean": "g/100g (percent)",
            "silt_30_100cm_mean": "g/100g (percent)",
            "silt_100_200cm_mean": "g/100g (percent)",
            "sand_0_30cm_mean": "g/100g (percent)",
            "sand_30_100cm_mean": "g/100g (percent)",
            "sand_100_200cm_mean": "g/100g (percent)",
            "coarse_fragments_0_30cm_mean": "cm^3/100cm^3(volpercent)",
            "coarse_fragments_30_100cm_mean": "cm^3/100cm^3(volpercent)",
            "coarse_fragments_100_200cm_mean": "cm^3/100cm^3(volpercent)",
            "bulk_density_0_30cm_mean": "kg/dm^3",
            "bulk_density_30_100cm_mean": "kg/dm^3",
            "bulk_density_100_200cm_mean": "kg/dm^3",
            "soil_organic_carbon_0_30cm_mean": "g/kg",
            "soil_organic_carbon_30_100cm_mean": "g/kg",
            "soil_organic_carbon_100_200cm_mean": "g/kg",
            "provider_id": "dimensionless",
            "gauge_name": "dimensionless",
            "water_body_name": "dimensionless",
            "federal_state": "dimensionless",
            "gauge_lat": "degree",
            "gauge_lon": "degree",
            "gauge_easting": "m",
            "gauge_northing": "m",
            "gauge_elev_metadata": "m.a.s.l.",
            "area_metadata": "km^2",
            "gauge_elev": "m.a.s.l.",
            "area": "km^2",
            "elev_mean": "m.a.s.l.",
            "elev_min": "m.a.s.l.",
            "elev_5": "m.a.s.l.",
            "elev_50": "m.a.s.l.",
            "elev_95": "m.a.s.l.",
            "elev_max": "m.a.s.l.",
        }
        return units_dict
