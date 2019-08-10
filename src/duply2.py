#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals


import os

from utils.logger import log
import utils.file_helper as fh
import utils.walker as walker
import utils.db_helper as db
import utils.hasher as hasher


def tests():
    userInput = "../"

    pathToScan = fh.normPath(userInput)
    listOfFiles = walker.get_list_of_files_in(pathToScan)

    databasePath = os.path.join(userInput, "index.db")
    db.checkConsistence(listOfFiles, databasePath)

    hasher.indexFiles(listOfFiles, databasePath)


if __name__ == '__main__':
    tests()
