"""Helpers for testing webassets.

This is included in the webassets package because it is useful for testing
external libraries that use webassets (like the flask-assets wrapper).
"""

import tempfile
import shutil
import os
from os import path
import time

from webassets import Environment, Bundle


__all__ = ('TempDirHelper', 'TempEnvironmentHelper',)


class TempDirHelper(object):
    """Base-class for tests which provides a temporary directory
    (which is properly deleted after the test is done), and various
    helper methods to do filesystem operations within that directory.
    """

    default_files = {}

    def setup(self):
        self._tempdir_created = tempfile.mkdtemp()
        self.create_files(self.default_files)

    def teardown(self):
        shutil.rmtree(self._tempdir_created)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, type, value, traceback):
        self.teardown()

    @property
    def tempdir(self):
        # Use a read-only property here, so the user is
        # less likely to modify the attribute, and have
        # his data deleted on teardown.
        return self._tempdir_created

    def create_files(self, files):
        """Helper that allows to quickly create a bunch of files in
        the media directory of the current test run.
        """
        # Allow passing a list of filenames to create empty files
        if not hasattr(files, 'items'):
            files = dict(map(lambda n: (n, ''), files))
        for name, data in files.items():
            dirs = path.dirname(self.path(name))
            if not path.exists(dirs):
                os.makedirs(dirs)
            f = open(self.path(name), 'w')
            f.write(data)
            f.close()

    def create_directories(self, *dirs):
        """Helper to create directories within the media directory
        of the current test's environment.
        """
        result = []
        for dir in dirs:
            full_path = self.path(dir)
            result.append(full_path)
            os.makedirs(full_path)
        return result

    def exists(self, name):
        """Ensure the given file exists within the current test run's
        media directory.
        """
        return path.exists(self.path(name))

    def get(self, name):
        """Return the given file's contents.
        """
        return open(self.path(name)).read()

    def path(self, name):
        """Return the given file's full path."""
        return path.join(self._tempdir_created, name)

    def setmtime(self, *files, **kwargs):
        """Set the mtime of the given files. Useful helper when
        needing to test things like the timestamp updater.

        Specify ``mtime`` as a keyword argument, or time.time()
        will automatically be used. Returns the mtime used.
        """
        mtime = kwargs.pop('mtime', time.time())
        assert not kwargs, "Unsupported kwargs: %s" %  ', '.join(kwargs.keys())
        for f in files:
            os.utime(self.path(f), (mtime, mtime))
        return mtime

    def p(self, *files):
        """Print the contents of the given files to stdout; useful
        for some quick debugging.
        """
        for f in files:
            print f
            print "-" * len(f)
            print self.get(f)
            print


class TempEnvironmentHelper(TempDirHelper):
    """Base-class for tests which provides a pre-created
    environment, based in a temporary directory, and utility
    methods to do filesystem operations within that directory.
    """

    default_files = {'in1': 'A', 'in2': 'B', 'in3': 'C', 'in4': 'D'}

    def setup(self):
        TempDirHelper.setup(self)

        # Not sure why this was called "m", but let's migrate
        # to self.env.
        self.m = self.env = self._create_environment()
        # Unless we explicitly test it, we don't want to use the cache
        # during testing.
        self.m.cache = False

    def _create_environment(self):
        return Environment(self._tempdir_created, '')

    def mkbundle(self, *a, **kw):
        b = Bundle(*a, **kw)
        b.env = self.m
        return b
