# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import imp
import os
import sys
import types
import uuid

class CoreImportHandler(object):
    """A custom import handler to allow for core version switching.

    Usage:
        >>> import sys
        >>> from tank.shotgun_deploy import CoreImportHandler
        >>> importer = CoreImportHandler("/path/to/a/version/of/tk-core")
        >>> sys.meta_path.append(importer)
        >>> # import/run a bunch of code
        >>> # context change, need to use a different core
        >>> importer.set_core_path("/path/to/a/different/version/of/tk-core")
        >>> # namespaces cleared out and re-imported from new core location
        >>> # new imports will come from new core location

    When an instance of this object is added to `sys.meta_path`, it is used to
    alter the way python imports packages.

    The core path is used to locate modules attempting to be loaded. The core
    path can be set via `set_core_path` to alter the location of future core
    imports.

    For more information on custom import hooks, see PEP 302:
        https://www.python.org/dev/peps/pep-0302/

    """

    def __init__(self, core_path):
        """Initialize the custom importer.

        :param core_path: A str path to the core location to import from.

        """

        self._core_path = None   # will be set shortly
        self._core_uuid = None
        self._namespaces = []

        # a dictionary to hold module information after it is found, before
        # it is loaded.
        self._module_info = {}

        # re-imports any existing modules for the core namespaces
        self.set_core_path(core_path)

    def __repr__(self):
        return (
            "<CoreImportHandler for core located in: '%s'" % (self.core_path,))

    def find_module(self, module_fullname, package_path=None):
        """Locates the given module in the current core.

        :param module_fullname: The fullname of the module to import
        :param package_path: None for a top-level module, or
            package.__path__ for submodules or subpackages

        For further info, see the docs on find_module here:
            https://docs.python.org/2/library/imp.html#imp.find_module

        :returns: this object (also a loader) if module found, None otherwise.
        """

        #if module_fullname == __name__:
        #    ## don't delete this module.
        #    return None
        #if module_fullname == "tank_vendor.shotgun_deploy.reload":
        #    return None

        # ---- see if an attempt has been made to locate the module already

        # get the package name from (first part of the module fullname)
        module_path_parts = module_fullname.split('.')
        package_name = module_path_parts[0]

        # make sure the package is in the list of supplied namespaces before
        # continuing.
        if package_name not in self._namespaces:
            # the package is not in one of the supplied namespaces, returning
            # None tells python to use the next importer available (likely the
            # default import mechanism).
            return None

        # see if this package is already loaded
        unique_module_fullname = self._get_unique_module_fullname(module_fullname)
        if unique_module_fullname in self._module_info:
            if self._module_info[unique_module_fullname]:
                # the module was previously found, return this object as the
                # object to load the module.
                return self
            else:
                # the module has been processed before but not found. return
                # None to fall back to the regular importer.
                return None

        if package_name == "sgtk":
            # ensure that the tank version of this module has been found and loaded
            sgtk_module_fullname = module_fullname
            if module_fullname == "sgtk":
                tank_module_fullname = "tank"
            else:
                tank_module_fullname = "%s.%s" % ("tank", ".".join(module_path_parts[1:]))

            unique_sgtk_module_fullname = unique_module_fullname
            unique_tank_module_fullname = self._get_unique_module_fullname(tank_module_fullname)

            # find the tank version if not already found
            if not unique_tank_module_fullname in self._module_info:
                if not self.find_module(tank_module_fullname):
                    # couldn't find it
                    return None

            # set the sgtk module info to match
            tank_module_info = self._module_info[unique_tank_module_fullname]
            self._module_info[unique_sgtk_module_fullname] = tank_module_info

            if tank_module_info:
                # already been searched and the module was found
                return self
            else:
                print "\n\n  *** HERE *** \n\n"
                return None

        # ensure parent packages loaded
        if len(module_path_parts) > 1:
            parent_module_fullname = ".".join(module_path_parts[:-1])
            unique_parent_module_fullname = self._get_unique_module_fullname(
                parent_module_fullname)
            if not unique_parent_module_fullname in self._module_info:
                print "FINDING: " + parent_module_fullname
                if self.find_module(parent_module_fullname):
                    self.load_module(parent_module_fullname)

        # ---- haven't tried to locate the module yet. try to find it now.

        # the name of the module (without the module path)
        module_name = module_path_parts[-1]

        # the module path as an actual partial path on disk
        if len(module_path_parts[0:-1]):
            module_path = os.path.join(*module_path_parts[0:-1])
        else:
            module_path = ""

        paths = [os.path.join(self.core_path, module_path)]

        try:
            # find the module and store its info in a lookup based on the
            # unique full module name. The module info is a tuple of the form:
            #   (file_obj, filename, description)
            # If this find is successful, we'll need the info in order
            # to load it later.
            module_info = imp.find_module(module_name, paths)
            self._module_info[unique_module_fullname] = module_info
            print "\n   FOUND MODULE: " + str(module_fullname)
            print "     PACKAGE_PATH: " + str(package_path)
        except ImportError:

            # see if the last part is an attribute
            parent_module_parts = module_path_parts[:-1]
            unique_parent_module_fullname = self._get_unique_module_fullname(
                ".".join(parent_module_parts)
            )
            if hasattr(sys.modules[unique_parent_module_fullname], module_path_parts[-1]):
                self._module_info[unique_module_fullname] = getattr(
                    sys.modules[unique_parent_module_fullname], module_path_parts[-1]
                )
                return self

            # no module found, fall back to regular import, and cache a value
            # of None so we don't try to search again.
            self._module_info[unique_module_fullname] = None
            print "\nCAN'T FIND MODULE: " + str(module_fullname)
            print "     PACKAGE_PATH: " + str(package_path)
            return None

        # module was found. since this object is also the "loader", return it
        return self

    def load_module(self, module_fullname):
        """Custom loader.

        Called by python if the find_module was successful.

        For further info, see the docs on `load_module` here:
            https://docs.python.org/2/library/imp.html#imp.load_module

        :param module_fullname: The fullname of the module to import

        :returns: The loaded module object.

        """

        # ---- see if the module has been imported into the unique namespace

        unique_module_fullname = self._get_unique_module_fullname(module_fullname)

        # the module has already been imported. return that module
        if unique_module_fullname in sys.modules:
            return sys.modules[unique_module_fullname]

        # ---- the module has not been imported. import it now

        file_obj = None
        try:
            module_info = self._module_info[unique_module_fullname]

            # retrieve the found module info
            if not module_info:
                print "\n\n**** OOPS: %s *****\n\n" % (unique_module_fullname,)

            if isinstance(module_info, types.ModuleType):
                module = module_info
                sys.modules[unique_module_fullname] = module_info
            else:
                (file_obj, filename, desc) = module_info
                print "\n\n  IMPORTING: " + module_fullname + " (%s)" % (unique_module_fullname,)

                # attempt to load the module given the info from find_module
                module = sys.modules.setdefault(
                    unique_module_fullname,
                    imp.load_module(unique_module_fullname, file_obj, filename, desc)
                )

            # get the package name from (first part of the module fullname)
            module_path_parts = module_fullname.split('.')
            package_name = module_path_parts[0]
            if package_name == "tank":
                module_path_parts[0] = "sgtk"
                # populate the sgtk namespace
                unique_sgtk_module_fullname = self._get_unique_module_fullname(
                    ".".join(module_path_parts)
                )
                sys.modules[unique_sgtk_module_fullname] = module
        except:
            print "\n\n\n **** RAISING IN LOAD ***** \n\n\n"
            raise
        finally:
            # as noted in the imp.load_module docs, must close the file handle.
            # we won't need it anymore even though a reference will be stored
            # in the `self._module_info` dict.
            if file_obj:
                file_obj.close()

        # the module needs to know the loader so that reload() works
        module.__loader__ = self

        # the module has been loaded from the proper core location!
        return module

    def set_core_path(self, path):
        """Set the core path to use.

        This method tells the import handler to import core namespaces form
        the supplied path. All future imports will look to this disk location.

        This method should be called at a high level, from a clean state in
        order to prevent import/compatibility conflicts with running code.

        :param path: str path to the core to import from.

        :raises: ValueError - if the supplied path does not exist or is not
            a valid directory.
        """

        # the paths are the same. No need to do anything.
        if path == self.core_path:
            return

        if not os.path.exists(path):
            raise ValueError(
                "The supplied core path is not a valid directory: '%s'."
                % (path,)
            )

        # TODO: ensure that the directory looks like core?

        # acquire a lock to prevent issues with other threads trying to import
        # while the switch is happening.
        imp.acquire_lock()

        # set the core path internally.
        self._core_path = path

        # go ahead and compute get a uuid to reuse
        self._core_uuid = uuid.uuid4().hex

        # get the new namespaces
        self._namespaces = [d for d in os.listdir(path) if not d.startswith(".")]

        # in order to allow our custom importer to work properly, we need to
        # remove any existing, non-uniquified modules from sys.modules. any
        # existing modules will prevent the the custom importer from running
        modules_to_delete = []
        for module_name in sys.modules:
            package_name = module_name.split(".")[0]
            if package_name in self._namespaces:
                modules_to_delete.append(module_name)

        # now delete the modules
        for module_name in modules_to_delete:
            if module_name == __name__:
                # don't delete this module.
                continue
            if module_name == "tank_vendor.shotgun_deploy.reload":
                continue
            print "DELETING: " + module_name
            del sys.modules[module_name]

        # release the lock so that other threads can continue importing from
        # the new core location.
        imp.release_lock()

    @property
    def core_path(self):
        """The core_path for this importer.

        :returns: str path to the core being used for imports
        """
        return self._core_path

    @property
    def namespaces(self):
        """The namespaces this importer operates on.

        :returns: a list where each item is a namespace str
        """
        return self._namespaces

    def _get_unique_module_fullname(self, module_fullname):
        return "%s_%s" % (self._core_uuid, module_fullname)
