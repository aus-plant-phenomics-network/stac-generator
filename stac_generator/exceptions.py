class SourceAssetException(Exception):
    """Exception raised when the source data cannot be read by itself"""


class SourceAssetLocationException(SourceAssetException):
    """Exception raised when the source asset location cannot be accessed"""


class TimezoneException(Exception):
    """Exception raised when timezone information cannot be determined from geometry"""


class StacConfigException(Exception):
    """Exception raised when the config metadata is misspecified"""


class ConfigFormatException(StacConfigException):
    """Exception raised when the format of the config is invalid"""


class InvalidExtensionException(StacConfigException):
    """Exception raised when the config extension is unsupported"""


class ColumnInfoException(StacConfigException):
    """Exception raised when information described in column info does not match source asset"""


class BandInfoException(StacConfigException):
    """Exception raised when information described in band info does not match raster asset"""


class JoinConfigException(StacConfigException):
    """Exception raised when information provided in join config is invalid"""
