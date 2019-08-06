#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals

import os
import tempfile
from datetime import datetime


def writeListToFile(list, filePrefix, nullsplit=True):
    """
    Writes an List of paths to a temp file
    :param list: list of path stings
    :param filePrefix: the prefix of the tmep file
    :returns: the path to the temp file
    """
    now = datetime.now()
    tempPrefix = filePrefix + now.strftime("%d_%m_%Y-%H_%M")
    new_file, path = tempfile.mkstemp(prefix=tempPrefix, text=True)

    splitter = "\x00"
    if not nullsplit:
        splitter = "\n"
    with os.fdopen(new_file, 'w') as tmp:
        for line in list:
            tmp.write(line + splitter)

    return path


def tests():
    list = ["/lol/flower/power", "/k/das/macht/", "/zu/viel/spaß"]
    path = writeListToFile(list, "cool")
    print(path)


if __name__ == '__main__':
    tests()
