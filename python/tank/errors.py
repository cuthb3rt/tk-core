# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
All custom exceptions that Tank emits are defined here.

"""

from tank_vendor.shotgun_base import ShotgunBaseError

# we alias this with TankError since this is what is commonly
# considered the top level exception in the toolkit world.
#
# 'tank' is a deprecated name and should be gracefully phased out
# over time.

TankError = ShotgunBaseError


class TankContextChangeNotSupportedError(TankError):
    """
    Exception that indicates that a requested context change is not allowed
    based on a check of the current engine and all of its active apps.
    """
    pass


class TankUnreadableFileError(TankError):
    """
    Exception that indicates that a required file can't be read from disk.
    """
    pass


class TankFileDoesNotExistError(TankUnreadableFileError):
    """
    Exceptions that indicates that a required file does not exist.
    """
    pass


class TankEngineInitError(TankError):
    """
    Exception that indicates that an engine could not start up.
    """
    pass


class TankErrorProjectIsSetup(TankError):
    """
    Exception that indicates that a project already has a toolkit name but no pipeline configuration.
    """

    def __init__(self):
        """
        Include error message
        """
        super(TankErrorProjectIsSetup, self).__init__("You are trying to set up a project which has already been set up. "
                                                      "If you want to do this, make sure to set the force parameter.")

class TankNoDefaultValueError(TankError):
    """
    Exception that can be raised when a default value is required but none is found.

    Typically raised by `tank.platform.bundle.resolve_default_value()` when the
    `raise_if_missing` flag is set to True.
    """
    pass
