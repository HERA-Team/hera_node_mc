from __future__ import print_function
from datetime import datetime
import os
import warnings


class HostsEthers:
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as fp:
            self.full_file = fp.read().splitlines()

    def rewrite_file(self):
        """
        Writes the contents of list "full_file" to the filename
        """
        if len(self.full_file) == 0:
            print("{} in memory to rewrite is empty - skipping"
                  .format(self.filename))
            return
        with open(self.filename, 'w') as fp:
            for line in self.full_file:
                print("{}".format(line), file=fp)

    def archive_file(self, path_to_archive='.', date_tag="%y%m%d-%H%M"):
        """
        Will copy the original file to new.

        Parameters
        ----------
        path_to_archive : str
            Path to which to write the new file.
        date_tag : str or bool(False)
            if not bool(False), will use that datetime format to tag the file.
        """
        fn = os.path.basename(self.filename)
        if date_tag:
            fn = "{}_{}".format(fn, datetime.strftime(datetime.now()))
        os.copy(self.filename, os.path.join(path_to_archive, fn))

    def read_hosts_ethers_file(self):
        """
        Read in the hosts or ethers file and send an e-mail on error.

        Attributes
        ----------
        by_id : dict
            entries with id (mac or ip) as key, listing all aliases
        by_alias : dict
            keyed on the aliases, value is the mac/ip
        """
        self.by_id = {}
        self.by_alias = {}
        for line in self.full_file:
            if line[0] == "#" or len(line) < 10:
                continue
            data = line.split()
            if data[0] in self.by_id.keys():
                msg = '{} is duplicated in {} file on {}'.format(data[0], self.filename)
                warnings.warn(msg)
            self.by_id[data[0]] = data[1:]
            for d in data[1:]:
                if d in self.by_id.keys():
                    msg = '{} is duplicated in {} file on {}'.format(data[0], self.filename)
                    warnings.warn(msg)
                self.by_alias[d] = data[0]
