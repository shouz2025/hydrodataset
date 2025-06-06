<!--
 * @Author: Wenyu Ouyang
 * @Date: 2021-12-05 22:13:21
 * @LastEditTime: 2024-10-15 14:32:16
 * @LastEditors: Wenyu Ouyang
 * @Description: README for hydrodataset
 * @FilePath: \hydrodataset\README.md
 * Copyright (c) 2021-2022 Wenyu Ouyang. All rights reserved.
-->
# hydrodataset


[![image](https://img.shields.io/pypi/v/hydrodataset.svg)](https://pypi.python.org/pypi/hydrodataset)
[![image](https://img.shields.io/conda/vn/conda-forge/hydrodataset.svg)](https://anaconda.org/conda-forge/hydrodataset)


**A Python package for downloading and reading hydrological datasets**

-   Free software: MIT license
-   Documentation: https://OuyangWenyu.github.io/hydrodataset

## Installation

It is quite easy to install hydrodataset. We provide a pip package to install:

```Bash
pip install hydrodataset
```

I highly recommend you to install this package in a virtual environment, so that it won't have negative impact on other packages in your base environment.

for example:

```Bash
# xxx is your env's name, such as hydrodataset
conda create -n xxx python=3.10
# activate the env
conda activate xxx
# install hydrodataset
conda install pip
pip install hydrodataset
```

## Usage

### 1. Download datasets

There are many datasets similar to CAMELS(-US), including CAMELS-AUS (Australia), CAMELS-BR (Brazil), CAMELS-CH (Switzerland), CAMELS-CL (Chile), CAMELS-DE (Germany), CAMELS-DK (Denmark), CAMELS-ES (Spain), CAMELS-FR (France), CAMELS-GB (Great Britain), CAMELS-IND (India), CAMELS-SE (Sweden), LamaH-CE, HYSETS. Recently, a new dataset named Caravan is released, which is a global dataset.

Now we only support auto-downloading for CAMELS-US (later for others), but I highly recommend you download them manually, as the downloading is not stable sometimes because of unstable web connections to the servers of these datasets in different places in the world.

the download links:

- [CAMELS-AUS (Australia)](https://doi.pangaea.de/10.1594/PANGAEA.921850)
- [CAMELS-BR (Brazil)](https://zenodo.org/record/3964745#.YNsjKOgzbIU)
- [CAMELS-CH (Switzerland)](https://zenodo.org/records/10354485)
- [CAMELS-CL (Chile)](https://doi.pangaea.de/10.1594/PANGAEA.894885)
- [CAMELS-DE (Germany)](https://zenodo.org/records/12733968)
- [CAMELS-DK (Denmark)](https://doi.org/10.22008/FK2/AZXSYP)
- [CAMELS-ES (Spain)](https://zenodo.org/records/8428374)
- [CAMELS-FR (France)](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/WH7FJR)
- [CAMELS-GB (Great Britain)](https://doi.org/10.5285/8344e4f3-d2ea-44f5-8afa-86d2987543a9)
- [CAMELS-IND (India)](https://zenodo.org/records/14005378)
- [CAMELS-SE (Sweden)](https://snd.se/sv/catalogue/dataset/2023-173/1)
- [CAMELS-US (United States)](https://gdex.ucar.edu/dataset/camels.html)
- [LamaH-CE (Central Europe)](https://doi.org/10.5281/zenodo.4525244)
- [HYSETS (North America)](https://osf.io/rpc3w/#!)
- [Caravan (Global)](https://zenodo.org/record/7944025)

put these downloaded files in the directory organized as follows:

```dir
camels/
├─ camels_aus/
│  ├─ 01_id_name_metadata.zip
│  ├─ 02_location_boundary_area.zip
│  ├─ 03_streamflow.zip
│  ├─ 04_attributes.zip
│  ├─ 05_hydrometeorology.zip
├─ camels_br/
│  ├─ 01_CAMELS_BR_attributes.zip
│  ├─ 02_CAMELS_BR_streamflow_m3s.zip
│  ├─ 03_CAMELS_BR_streamflow_mm_selected_catchments.zip
│  ├─ 04_CAMELS_BR_streamflow_simulated.zip
│  ├─ 05_CAMELS_BR_precipitation_chirps.zip
│  ├─ 06_CAMELS_BR_precipitation_mswep.zip
│  ├─ 07_CAMELS_BR_precipitation_cpc.zip
│  ├─ 08_CAMELS_BR_evapotransp_gleam.zip
│  ├─ 09_CAMELS_BR_evapotransp_mgb.zip
│  ├─ 10_CAMELS_BR_potential_evapotransp_gleam.zip
│  ├─ 11_CAMELS_BR_temperature_min_cpc.zip
│  ├─ 12_CAMELS_BR_temperature_mean_cpc.zip
│  ├─ 13_CAMELS_BR_temperature_max_cpc.zip
│  ├─ 14_CAMELS_BR_catchment_boundaries.zip
│  ├─ 15_CAMELS_BR_gauges_location_shapefile.zip
├─ camels_ch/
│  ├─ camels_ch.zip
├─ camels_cl/
│  ├─ 10_CAMELScl_tmean_cr2met.zip
│  ├─ 11_CAMELScl_pet_8d_modis.zip
│  ├─ 12_CAMELScl_pet_hargreaves.zip
│  ├─ 13_CAMELScl_swe.zip
│  ├─ 14_CAMELScl_catch_hierarchy.zip
│  ├─ 1_CAMELScl_attributes.zip
│  ├─ 2_CAMELScl_streamflow_m3s.zip
│  ├─ 3_CAMELScl_streamflow_mm.zip
│  ├─ 4_CAMELScl_precip_cr2met.zip
│  ├─ 5_CAMELScl_precip_chirps.zip
│  ├─ 6_CAMELScl_precip_mswep.zip
│  ├─ 7_CAMELScl_precip_tmpa.zip
│  ├─ 8_CAMELScl_tmin_cr2met.zip
│  ├─ 9_CAMELScl_tmax_cr2met.zip
│  ├─ CAMELScl_catchment_boundaries.zip
├─ camels_de/
│  ├─ camels_de.zip
├─ camels_dk/
│  ├─ Attributes
│  ├─ Dynamics
│  ├─ Shapefile
├─ camels_es/
│  ├─ attributes
│  ├─ licenses
│  ├─ shapefiles
│  ├─ timeseries
│  ├─ README.md
├─ camels_fr/
│  ├─ ADDITIONAL_LICENSES
│  ├─ CAMELS_FR_attributes
│  ├─ CAMELS_FR_geography
│  ├─ CAMELS_FR_time_series
│  ├─ CAMELS-FR_description.ods
│  ├─ MANIFEST.TXT
│  ├─ README.md
├─ camels_gb/
│  ├─ 8344e4f3-d2ea-44f5-8afa-86d2987543a9.zip
├─ camels_ind/
│  ├─ CAMELS_IND_All_Catchments
│  ├─ CAMELS_IND_Catchments_Streamflow_Sufficient
├─ camels_se/
│  ├─ catchment properties.zip
│  ├─ catchment time series.zip
│  ├─ catchment_GIS_shapefiles.zip
├─ camels_us/
│  ├─ basin_set_full_res.zip
│  ├─ basin_timeseries_v1p2_metForcing_obsFlow.zip
│  ├─ basin_timeseries_v1p2_modelOutput_daymet.zip
│  ├─ basin_timeseries_v1p2_modelOutput_maurer.zip
│  ├─ basin_timeseries_v1p2_modelOutput_nldas.zip
│  ├─ camels_attributes_v2.0.xlsx
│  ├─ camels_clim.txt
│  ├─ camels_geol.txt
│  ├─ camels_hydro.txt
│  ├─ camels_name.txt
│  ├─ camels_soil.txt
│  ├─ camels_topo.txt
│  ├─ camels_vege.txt
lamah_ce/
├─ 2_LamaH-CE_daily
hysets/
├─ HYSETS_2020_QC_stations.nc
├─ HYSETS_watershed_boundaries.zip
├─ HYSETS_watershed_properties.txt
caravan/
├─ Caravan.zip
├─ Caravan_extension_CH.zip
```

### 2. Run the code

First, run the following Python code:

```Python
import hydrodataset
```

then in your home directory, you will find the directory for hydrodataset:

- Windows: C:\\Users\\xxx\\hydro_setting.yml (xxx is your username))
- Ubuntu: /home/xxx/hydro_setting.yml

The hydro_setting.yml file is a config file including some specific path for your datasets and some credentials for your database, such as minio and postgres.

**NOTE: For this repository, we only need the "datasets-origin" of "local_data_path", so just fill in the path for "datasets-origin" in the "local_data_path" section, and leave other fields empty.**

```YAML
minio:
  server_url: ''
  client_endpoint: ''
  access_key: ''
  secret: ''

local_data_path:
  root: ''
  datasets-origin: 'D:\data\waterism\datasets-origin' # set your path here
  datasets-interim: ''
  basins-origin: ''
  basins-interim: ''
postgres:
  server_url: ''
  port: 0
  username: ''
  password: ''
  database: ''
```

Then, you can use functions in hydrodataset, examples could be seen **here: https://github.com/OuyangWenyu/hydrodataset/blob/main/examples/scripts.py**

**NOTE: Please don't modify the interface of the functions in hydrodataset, as it may cause some errors, unless one can entirely refactor the code.**

These functions are about reading attributes/forcing/streamflow data.

**When you first run the code, you should set the parameter "download" to True**:

```Python
import os
from hydrodataset.camels import Camels
camels = Camels(data_path=os.path.join("camels", "camels_us"), download=True, region="US")
```

It will unzip all downloaded files, and take some minutes, please be patient.

**Except for the first run, you should set "download" to False**:

```Python
import os
from hydrodataset.camels import Camels
# default is False
camels = Camels(data_path=os.path.join("camels", "camels_us"), region="US")
```

You can change your data_path to anywhere you put in the the root directory of hydrodataset.

## Features

HydroDataset is designed to help (1) download, (2) read, (3)format and (4) visualize some datasets through a
core language (Python) for watershed hydrological modeling.

**Note**: But now this repository is still developing and only supports quite simple functions such as downloading and reading data for watersheds.

Now the dataset zoo list includes:

| **Number** | **Dataset** | **Description**                                                               |
| ---------- | ----------- |-------------------------------------------------------------------------------|
| 1          | **CAMELS**  | CAMELS series datasets including CAMELS-AUS/BR/CH/CL/DE/DK/ES/FR/GB/IND/SE/US |
| 2          | **LamaH**   | LamaH-CE dataset for Central Europe                                           |
| 3          | **HYSETS**  | HYSETS dataset for North America                                              |
| 4          | **Caravan** | Caravan dataset for global                                                    |

For CAMELS-ES, we didn't finish reading functions yet, but we will finish it soon.

We highly recommend you to use [xarray](http://xarray.pydata.org/en/stable/) to read the data, as it is a powerful tool for handling multi-dimensional data. Then, you can see the units of all variables in the xarray dataset. For US, we provide full support for reading attributes, forcing, and streamflow data with such a cache-reading support, so that you can read them quickly after the first time you read them.

For others, we only provide support for reading without cache-reading support, so it may take some time to read them. We will finish cache-reading support for them soon.

For units, we use [pint](https://github.com/hgrecco/pint), and [pint-xarray](https://github.com/xarray-contrib/pint-xarray) to handle them.

## Credits

This package was created with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [giswqs/pypackage](https://github.com/giswqs/pypackage) project template.

It was inspired by [HydroData](https://github.com/mikejohnson51/HydroData) and used some tools made by [cheginit](https://github.com/cheginit).
