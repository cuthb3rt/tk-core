# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from ..errors import TankError


class MissingConfigurationFileError(TankError):
    """
    Thrown when an environment variable specific a location for a configuration
    file that doesn't exist.
    """

    def __init__(self, var_name, path):
        """
        Constructor.

        :param str var_name: Name of the environment variable used.
        :param str path: Path to the configuration file that doesn't exist.
        """
        TankError.__init__(
            self,
            "The environment variable '%s' refers to a configuration file on disk at '%s' that doesn't exist." % (
                var_name,
                path
            )
        )