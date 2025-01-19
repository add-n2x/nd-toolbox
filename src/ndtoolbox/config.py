"""App configuration."""

import logging
import os

import colorlog
import confuse


class Config(confuse.Configuration):
    """
    Configuration for application based on Confuse.
    """

    logger: logging.Logger = None

    def __init__(self, app_name: str):
        """Init configuration."""
        super().__init__(app_name)
        super().set_file("config/config.yaml")
        dir_data = self["data"].get(str)
        file_duplicates_json = os.path.join(dir_data, "beets/beets-duplicates.json")
        file_data_json = os.path.join(dir_data, "nd-toolbox-data.json")
        file_error_json = os.path.join(dir_data, "nd-toolbox-error.json")
        file_log = os.path.join(dir_data, "nd-toolbox.log")
        self.set_args(
            {
                "FILE_BEETS_INPUT_JSON": file_duplicates_json,
                "FILE_TOOLBOX_DATA_JSON": file_data_json,
                "ERROR_REPORT_JSON": file_error_json,
                "file-log": file_log,
            }
        )
        self.init_logger()

    def init_logger(self):
        """Setup logger."""
        log_level = self["log-level"].get(str)
        file_log = self["file-log"].get(str)
        if log_level not in logging._nameToLevel:
            raise ValueError(f"Invalid log-level: {log_level}")
        self.logger = colorlog.getLogger("ndtoolbox")

        colorlog.basicConfig(
            filename=file_log,
            filemode="w",
            encoding="utf-8",
            level=log_level,
            format="%(log_color)s %(msecs)d %(name)s %(levelname)s %(message)s",
        )
        self.logger.info(f"Initialized logger with level: {log_level} and log file: {file_log}")


config = Config("Heartbeets")
