import logging
from typing import Any

import geopandas as gpd
import pandas as pd
import pystac

from stac_generator._types import CsvMediaType
from stac_generator.base.generator import VectorGenerator
from stac_generator.csv.schema import ColumnInfo, CsvConfig, CsvExtension

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
    logger.debug(f"reading csv from path: {src_path}")
    parse_dates: list[str] | bool = [T_coord] if isinstance(T_coord, str) else False
    usecols: list[str] | None = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if columns:
        usecols = [item["name"] if isinstance(item, dict) else item for item in columns]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        if Z_coord:
            usecols.append(Z_coord)
    df = pd.read_csv(
        filepath_or_buffer=src_path,
        usecols=usecols,
        date_format=date_format,
        parse_dates=parse_dates,
    )
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


class CsvGenerator(VectorGenerator[CsvConfig]):
    def __init__(
        self,
        configs: list[dict[str, Any]],
    ) -> None:
        super().__init__(
            configs=configs,
        )

    def create_item_from_config(self, source_cfg: CsvConfig) -> pystac.Item:
        assets = {
            "data": pystac.Asset(
                href=source_cfg.location,
                description="Raw csv data",
                roles=["data"],
                media_type=CsvMediaType,
            )
        }
        raw_df = read_csv(
            source_cfg.location,
            source_cfg.X,
            source_cfg.Y,
            source_cfg.epsg,
            source_cfg.Z,
            source_cfg.T,
            source_cfg.date_format,
            source_cfg.column_info,
        )

        properties = CsvExtension.model_validate(source_cfg, from_attributes=True).model_dump()
        return self.df_to_item(
            raw_df,
            assets,
            source_cfg,
            properties,
            source_cfg.T,
            source_cfg.epsg,
        )
