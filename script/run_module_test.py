import datetime
from typing import Any

from stac_generator.core.base.generator import StacSerialiser
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.raster.schema import RasterConfig
from stac_generator.core.vector.schema import VectorConfig
from stac_generator.factory import StacGeneratorFactory

point_config: list[dict[str, Any]] = [
    {
        "id": "adelaide_airport",
        "location": "tests/files/integration_tests/point/data/adelaide_airport.csv",
        "collection_date": "2023-01-01",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {"name": "max_temp", "description": "Observed daily maximum temperature in degree C"},
            {"name": "min_temp", "description": "Observed daily minimum temperature in degree C"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
            {"name": "mslp", "description": "Mean sea level pressure in hPa"},
        ],
    },
    {
        "id": "adelaide_salisbury_bowling_club",
        "location": "tests/files/integration_tests/point/data/adelaide_salisbury_bowling_club.csv",
        "collection_date": "2023-01-02",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
        ],
    },
    {
        "id": "aston_coop",
        "location": "tests/files/integration_tests/point/data/aston_coop.csv",
        "collection_date": "2023-01-03",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {"name": "max_temp", "description": "Observed daily maximum temperature in degree C"},
            {"name": "min_temp", "description": "Observed daily minimum temperature in degree C"},
        ],
    },
    {
        "id": "belair",
        "location": "tests/files/integration_tests/point/data/belair.csv",
        "collection_date": "2023-01-04",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [{"name": "daily_rain", "description": "Observed daily rain fall in mm"}],
    },
    {
        "id": "edinburg_raaf",
        "location": "tests/files/integration_tests/point/data/edinburg_raaf.csv",
        "collection_date": "2023-01-05",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {"name": "max_temp", "description": "Observed daily maximum temperature in degree C"},
            {"name": "min_temp", "description": "Observed daily minimum temperature in degree C"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
            {"name": "mslp", "description": "Mean sea level pressure in hPa"},
        ],
    },
    {
        "id": "glen_osmond",
        "location": "tests/files/integration_tests/point/data/glen_osmond.csv",
        "collection_date": "2023-01-06",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
        ],
    },
    {
        "id": "happy_valley_reservoir",
        "location": "tests/files/integration_tests/point/data/happy_valley_reservoir.csv",
        "collection_date": "2023-01-07",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [{"name": "daily_rain", "description": "Observed daily rain fall in mm"}],
    },
    {
        "id": "hope_valley_reservoir",
        "location": "tests/files/integration_tests/point/data/hope_valley_reservoir.csv",
        "collection_date": "2023-01-08",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
        ],
    },
    {
        "id": "north_adelaide",
        "location": "tests/files/integration_tests/point/data/north_adelaide.csv",
        "collection_date": "2023-01-09",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
            {"name": "daily_rain", "description": "Observed daily rain fall in mm"},
            {
                "name": "radiation",
                "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm",
            },
        ],
    },
    {
        "id": "soil_data",
        "location": "tests/files/integration_tests/point/data/soil_data.csv",
        "collection_date": "2023-01-01",
        "collection_time": "09:00:00",
        "X": "Longitude",
        "Y": "Latitude",
        "Z": "mid_depth",
        "T": None,
        "epsg": 4326,
        "column_info": [{"name": "Ca_Soln", "description": "Ca concentration"}],
    },
]

raster_config = RasterConfig(
    id="L2A_PVI",
    location="tests/files/integration_tests/raster/data/L2A_PVI.tif",
    collection_date=datetime.datetime.strptime("2021-02-21", "%Y-%m-%d").date(),  # noqa: DTZ007
    collection_time=datetime.datetime.strptime("10:00:17", "%H:%M:%S").time(),  # noqa: DTZ007
    epsg=32633,
    band_info=[
        {
            "name": "B04",
            "common_name": "red",
            "description": "Common name: red, Range: 0.6 to 0.7",
            "wavelength": 0.6645,
        },
        {
            "name": "B03",
            "common_name": "green",
            "description": "Common name: green, Range: 0.5 to 0.6",
            "wavelength": 0.56,
        },
        {
            "name": "B02",
            "common_name": "blue",
            "description": "Common name: blue, Range: 0.45 to 0.5",
            "wavelength": 0.4966,
        },
    ],
)

vector_dict_config = [
    {
        "id": "lga",
        "location": "tests/files/integration_tests/vector/data/lga.gpkg",
        "collection_date": "2023-04-01",
        "collection_time": "09:00:00",
        "epsg": 3857,
        "column_info": [
            {"name": "objectid", "description": "object id"},
            {"name": "lga_code_2019", "description": "LGA code 2019 survey"},
            {"name": "lga_name_2019", "description": "LGA name 2019 survey"},
            {"name": "state_code_2016", "description": "State code 2016 survey"},
            {"name": "state_name_2016", "description": "State name 2016 survey"},
            {
                "name": "area_albers_sqkm",
                "description": "Feature area in Albers projection - sq km",
            },
            {"name": "st_length(shape)", "description": "Shape length"},
            {"name": "st_area(shape)", "description": "Shape area"},
        ],
    },
    {
        "id": "soil_exposure",
        "title": "soil exposure data - DEWNR Soil and Land Program",
        "description": "Exposure of land to wind, and to some extent to the sun, on west facing slopes can significantly reduce productivity. Assessment of exposure is highly subjective, and is designed to do no more than signal that it is a factor to consider in certain situations. Exposure is simply assessed for the purposes of this classification by judging whether or not the land is unprotected by nearby high ground. Three Exposure attribute classes are considered: Y1, Y2, Y3. Assessments are based on an interpretation of Soil landscape map units which are categorised into legend categories according to the proportion of the landscape with the highest degree of exposure, provided that it accounts for at least 30% of the area of the map unit.",
        "location": "tests/files/integration_tests/vector/data/soil_exposure.geojson",
        "collection_date": "2016-06-09",
        "collection_time": "09:00:00",
        "epsg": 7844,
        "column_info": [
            {
                "name": "LANSLU",
                "description": "Soil Landscape Map Unit (LANSLU code): Concatenation of Land System (LANDSYSTEM code) and Soil Landscape Unit (SLU code). Link item to join spatial data with other tables.",
            },
            {"name": "OBJECTID", "description": "object id"},
            {
                "name": "EXPOSURE",
                "description": "Degree of exposure (Legend category. See layer file for descriptions).",
            },
            {
                "name": "Y1",
                "description": "Percentage of map unit with low exposure. Attribute Class: Y1, Degree of exposure: Low, Relevant situations: Land other than above.",
            },
            {
                "name": "Y2",
                "description": "Percentage of map unit with moderate exposure. Attribute Class: Y2, Degree of exposure: Moderate, Relevant situations: Plateaux or summit surfaces of higher elevation than the surrounding terrain; Hillslopes adjacent to extensive lower lying land (e.g. escarpments bordering plains); Upper slopes projecting above neighbouring hills; Moderate to high sandhills; Land within five km of the coast and with direct line of sight to the sea.",
            },
            {
                "name": "Y3",
                "description": "Percentage of map unit with high exposure. Attribute Class: Y3, Degree of exposure: High, Relevant situations: Land within five km of the coast and with direct line of sight to the sea.",
            },
            {
                "name": "YX",
                "description": "Percentage of map unit which is not applicable. Attribute Class: YX, Not Applicable",
            },
            {"name": "SHAPE_Length", "description": "Shape length"},
            {"name": "SHAPE_Area", "description": "Shape area"},
        ],
    },
    {
        "id": "soil_subgroup",
        "title": "soil subgroup data - DEWNR Soil and Land Program",
        "description": "61 soils have been identified, representative of the range occurring across southern South Australia, based on an interpretation of Soil Landscape Map Units. These Soils (soil type) classes are also termed 'subgroup soils' in the reference text Hall et al. 2009, 'The Soils of Southern South Australia', where they are described in detail. Each of these soils has a two character alphanumeric code. The first character (letter) represents the relevant Soil GroupSELECT 1 FROM DUAL; the second character (number) represents a particular Soil within the Soil Group. Three additional miscellaneous classes (rock, water, not applicable) are also provided. Hence, 64 attribute (or 'analysis data') classes have been supplied, as percentage (areal extent) values of each possible soil type within each Soil Landscape Map Unit. Note: the sum of all percentage values for each map unit totals 100%. This analysis data is to be used for the creation of spatial data statistics. For map display purposes, the most commonly occurring Soil (SOIL_SUBGR legend category) is defined, however, it should be noted that this often accounts for less than 50% of a Soil Landscape Map Unit.",
        "location": "tests/files/integration_tests/vector/data/soil_subgroup.zip",
        "collection_date": "2016-06-09",
        "collection_time": "09:00:00",
        "epsg": 1168,
        "column_info": [
            {
                "name": "LANSLU",
                "description": "Soil Landscape Map Unit (LANSLU code): Concatenation of Land System (LANDSYSTEM code) and Soil Landscape Unit (SLU code). Link item to join spatial data with other tables.",
            },
            {"name": "OBJECTID", "description": "object id"},
            {
                "name": "SOIL_SUBGR",
                "description": "MOST COMMON SOIL TYPE in map unit (Legend category. See layer file for descriptions)",
            },
            {"name": "SHAPE_Area", "description": "Shape area"},
            {
                "name": "A1",
                "description": "Percentage of A1 soil (Highly calcareous sandy loam) in map unit",
            },
            {
                "name": "A2",
                "description": "Percentage of A2 soil (Calcareous loam on rock) in map unit",
            },
            {
                "name": "A3",
                "description": "Percentage of A3 soil (Moderately calcareous loam) in map unit",
            },
            {
                "name": "A4",
                "description": "Percentage of A4 soil (Calcareous loam) in map unit",
            },
            {
                "name": "A5",
                "description": "Percentage of A5 soil (Calcareous loam on clay) in map unit",
            },
            {
                "name": "A6",
                "description": "Percentage of A6 soil (Calcareous gradational clay loam) in map unit",
            },
            {
                "name": "A7",
                "description": "Percentage of A7 soil (Calcareous clay loam on marl) in map unit",
            },
            {
                "name": "A8",
                "description": "Percentage of A8 soil (Gypseous calcareous loam) in map unit",
            },
            {
                "name": "B1",
                "description": "Percentage of B1 soil (Shallow highly calcareous sandy loam on calcrete) in map unit",
            },
            {
                "name": "B2",
                "description": "Percentage of B2 soil (Shallow calcareous loam on calcrete) in map unit",
            },
            {
                "name": "B3",
                "description": "Percentage of B3 soil (Shallow sandy loam on calcrete) in map unit",
            },
            {
                "name": "B4",
                "description": "Percentage of B4 soil (Shallow red loam on limestone) in map unit",
            },
            {
                "name": "B5",
                "description": "Percentage of B5 soil (Shallow dark clay loam on limestone) in map unit",
            },
            {
                "name": "B6",
                "description": "Percentage of B6 soil (Shallow loam over red clay on calcrete) in map unit",
            },
            {
                "name": "B7",
                "description": "Percentage of B7 soil (Shallow sand over clay on calcrete) in map unit",
            },
            {
                "name": "B8",
                "description": "Percentage of B8 soil (Shallow sand on calcrete) in map unit",
            },
            {
                "name": "B9",
                "description": "Percentage of B9 soil (Shallow clay loam over brown or dark clay on calcrete) in map unit",
            },
            {
                "name": "C1",
                "description": "Percentage of C1 soil (Gradational sandy loam) in map unit",
            },
            {
                "name": "C2",
                "description": "Percentage of C2 soil (Gradational loam on rock) in map unit",
            },
            {
                "name": "C3",
                "description": "Percentage of C3 soil (Friable gradational clay loam) in map unit",
            },
            {
                "name": "C4",
                "description": "Percentage of C4 soil (Hard gradational clay loam) in map unit",
            },
            {
                "name": "C5",
                "description": "Percentage of C5 soil (Dark gradational clay loam) in map unit",
            },
            {
                "name": "D1",
                "description": "Percentage of D1 soil (Loam over clay on rock) in map unit",
            },
            {
                "name": "D2",
                "description": "Percentage of D2 soil (Loam over red clay) in map unit",
            },
            {
                "name": "D3",
                "description": "Percentage of D3 soil (Loam over poorly structured red clay) in map unit",
            },
            {
                "name": "D4",
                "description": "Percentage of D4 soil (Loam over pedaric red clay) in map unit",
            },
            {
                "name": "D5",
                "description": "Percentage of D5 soil (Hard loamy sand over red clay) in map unit",
            },
            {
                "name": "D6",
                "description": "Percentage of D6 soil (Ironstone gravelly sandy loam over red clay) in map unit",
            },
            {
                "name": "D7",
                "description": "Percentage of D7 soil (Loam over poorly structured clay on rock) in map unit",
            },
            {
                "name": "E1",
                "description": "Percentage of E1 soil (Black cracking clay) in map unit",
            },
            {
                "name": "E2",
                "description": "Percentage of E2 soil (Red cracking clay) in map unit",
            },
            {
                "name": "E3",
                "description": "Percentage of E3 soil (Brown or grey cracking clay) in map unit",
            },
            {
                "name": "F1",
                "description": "Percentage of F1 soil (Loam over brown or dark clay) in map unit",
            },
            {
                "name": "F2",
                "description": "Percentage of F2 soil (Sandy loam over poorly structured brown or dark clay) in map unit",
            },
            {
                "name": "G1",
                "description": "Percentage of G1 soil (Sand over sandy clay loam) in map unit",
            },
            {
                "name": "G2",
                "description": "Percentage of G2 soil (Bleached sand over sandy clay loam) in map unit",
            },
            {
                "name": "G3",
                "description": "Percentage of G3 soil (Thick sand over clay) in map unit",
            },
            {
                "name": "G4",
                "description": "Percentage of G4 soil (Sand over poorly structured clay) in map unit",
            },
            {"name": "H1", "description": "Percentage of H1 soil (Carbonate sand) in map unit"},
            {"name": "H2", "description": "Percentage of H2 soil (Siliceous sand) in map unit"},
            {
                "name": "H3",
                "description": "Percentage of H3 soil (Bleached siliceous sand) in map unit",
            },
            {
                "name": "I1",
                "description": "Percentage of I1 soil (Highly leached sand) in map unit",
            },
            {
                "name": "I2",
                "description": "Percentage of I2 soil (Wet highly leached sand) in map unit",
            },
            {
                "name": "J1",
                "description": "Percentage of J1 soil (Ironstone soil with alkaline lower subsoil) in map unit",
            },
            {"name": "J2", "description": "Percentage of J2 soil (Ironstone soil) in map unit"},
            {
                "name": "J3",
                "description": "Percentage of J3 soil (Shallow soil on ferricrete) in map unit",
            },
            {
                "name": "K1",
                "description": "Percentage of K1 soil (Acidic gradational loam on rock) in map unit",
            },
            {
                "name": "K2",
                "description": "Percentage of K2 soil (Acidic loam over clay on rock) in map unit",
            },
            {
                "name": "K3",
                "description": "Percentage of K3 soil (Acidic sandy loam over red clay on rock) in map unit",
            },
            {
                "name": "K4",
                "description": "Percentage of K4 soil (Acidic sandy loam over brown or grey clay on rock) in map unit",
            },
            {
                "name": "K5",
                "description": "Percentage of K5 soil (Acidic gradational sandy loam on rock) in map unit",
            },
            {
                "name": "L1",
                "description": "Percentage of L1 soil (Shallow soil on rock) in map unit",
            },
            {
                "name": "M1",
                "description": "Percentage of M1 soil (Deep sandy loam) in map unit",
            },
            {
                "name": "M2",
                "description": "Percentage of M2 soil (Deep friable gradational clay loam) in map unit",
            },
            {
                "name": "M3",
                "description": "Percentage of M3 soil (Deep gravelly soil) in map unit",
            },
            {
                "name": "M4",
                "description": "Percentage of M4 soil (Deep hard gradational sandy loam) in map unit",
            },
            {"name": "N1", "description": "Percentage of N1 soil (Peat) in map unit"},
            {"name": "N2", "description": "Percentage of N2 soil (Saline soil) in map unit"},
            {
                "name": "N3",
                "description": "Percentage of N3 soil (Wet soil (non to moderately saline) in map unit",
            },
            {
                "name": "O1",
                "description": "Percentage of O1 soil (Volcanic ash soil) in map unit",
            },
            {"name": "RR", "description": "Percentage of RR (Rock) in map unit"},
            {"name": "WW", "description": "Percentage of WW (Water) in map unit"},
            {"name": "XX", "description": "Percentage of map unit which is not applicable"},
        ],
    },
    {
        "id": "waite_oval",
        "location": "tests/files/integration_tests/vector/data/waite_oval.geojson",
        "title": "waite oval mask",
        "description": "waite oval mask",
        "epsg": 4326,
        "collection_date": "2024-01-01",
        "collection_time": "09:00:00",
    },
]

vector_config = [VectorConfig.model_validate(item) for item in vector_dict_config]

collection_config = StacCollectionConfig(id="collection", description="Auto-generated Stac Item")

generator = StacGeneratorFactory.get_stac_generator(
    (point_config, raster_config, vector_config), collection_config
)

serialiser = StacSerialiser(generator, "example/generated/module")
serialiser()
