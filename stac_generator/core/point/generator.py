import logging
from typing import Any

import geopandas as gpd
import pystac

from stac_generator._types import CsvMediaType
from stac_generator.core.base.generator import VectorGenerator
from stac_generator.core.base.schema import ColumnInfo
from stac_generator.core.base.utils import _read_csv
from stac_generator.core.point.schema import PointConfig

logger = logging.getLogger(__name__)


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    epsg: int,
    Z_coord: str | None = None,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    columns: list[str] | list[ColumnInfo] | None = None,
) -> gpd.GeoDataFrame:
    """Read in csv from local disk

    Users must provide at the bare minimum the location of the csv, and the names of the columns to be
    treated as the X and Y coordinates. By default, will read in all columns in the csv. If columns and groupby
    columns are provided, will selectively read specified columns together with the coordinate columns (X, Y, T).

    :param src_path: path to csv file
    :type src_path: str
    :param X_coord: name of X field
    :type X_coord: str
    :param Y_coord: name of Y field
    :type Y_coord: str
    :param epsg: epsg code
    :type epsg: int
    :param Z_coord: name of Z field
    :type Z_coord: str
    :param T_coord: name of time field, defaults to None
    :type T_coord: str | None, optional
    :param date_format: format to pass to pandas to parse datetime, defaults to "ISO8601"
    :type date_format: str, optional
    :param columns: band information, defaults to None
    :type columns: list[str] | list[ColumnInfo] | None, optional
    :return: read dataframe
    :rtype: pd.DataFrame
    """
    df = _read_csv(
        src_path=src_path,
        required=[X_coord, Y_coord],
        optional=[Z_coord] if Z_coord else None,
        date_col=T_coord,
        date_format=date_format,
        columns=columns,
    )

    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


class PointGenerator(VectorGenerator[PointConfig]):
    """ItemGenerator class that handles point data in csv format"""

    @staticmethod
    def create_config(source_config: dict[str, Any]) -> dict[str, Any]:
        if "X" not in source_config or "Y" not in source_config or "epsg" not in source_config:
            raise ValueError(
                f"Expects X and Y column to be described in source config for item: {source_config['id']}"
            )
        raw_df = read_csv(
            source_config["id"],
            source_config["X"],
            source_config["Y"],
            source_config["epsg"],
            source_config.get("Z"),
            source_config.get("T"),
            source_config.get("date_format", "ISO8601"),
        )
        columns = set(raw_df.columns) - {
            source_config["id"],
            source_config["X"],
            source_config["Y"],
            source_config.get("Z"),
            source_config.get("T"),
        }
        column_info = []
        for col in columns:
            column_info.append(ColumnInfo(name=col, description=f"{col}_description"))
        return PointConfig(**source_config, column_info=column_info).to_properties()

    def create_item_from_config(self, source_config: PointConfig) -> pystac.Item:
        """Create item from source csv config

        :param source_config: config which contains csv metadata
        :type source_config: PointConfig
        :return: stac metadata of the item described in source_config
        :rtype: pystac.Item
        """
        assets = {
            "data": pystac.Asset(
                href=source_config.location,
                description="Raw csv data",
                roles=["data"],
                media_type=CsvMediaType,
            )
        }
        raw_df = read_csv(
            source_config.location,
            source_config.X,
            source_config.Y,
            source_config.epsg,
            source_config.Z,
            source_config.T,
            source_config.date_format,
            source_config.column_info,
        )
        if source_config.T is not None:
            start_datetime = raw_df[source_config.T].min()
            end_datetime = raw_df[source_config.T].max()
        else:
            start_datetime, end_datetime = None, None

        properties = source_config.to_properties()
        return self.df_to_item(
            raw_df,
            assets,
            source_config,
            properties,
            source_config.epsg,
            start_datetime,
            end_datetime,
        )
