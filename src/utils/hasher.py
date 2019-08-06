#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals

import os
import time
import hashlib

from logger import log
import db_helper


def indexFiles(fileList, database):
    """
    Index files into database with short-hash and long hash
    :param fileList: list of files to be indexed, Array of
    dictionaries {path, size, modified_date}
    :param database: database file
    """
    basePath = os.path.dirname(database)
    log('Index files in: file://%s ....' % basePath, 0)
    conn = db_helper.create(database)

    lastInfoTime = time.time()
    countDoneFiles = 0

    for file in fileList:
        countDoneFiles += 1
        dbFile = db_helper.get_entry_by_path(conn, file["path"])
        if dbFile is not None:
            if dbFile["size"] == file["size"] and dbFile["modified_date"] == file["modified_date"]:
                continue
            else:
                db_helper.delete_by_path(conn, file["path"])

        fileName = os.path.koin(basePath, file["path"])

        openedFile = file(fileName, 'r')
        hasher = hashlib.sha1()
        countHashedBlocks = 0
        while True:
            r = openedFile.read(4096)
            if not len(r):
                break
            hasher.update(r)
            countHashedBlocks += 1
            if countHashedBlocks >= 2560:
                # Maximal hash the first 10mb
                break
        openedFile.close()
        hashValue = hasher.digest()
        file["hash"] = hashValue
        db_helper.insert_entry(conn, file)

        if time.time() - lastInfoTime >= 5:
            lastInfoTime = time.time()
            db_helper.commit(conn)
            log("Still index files in the path... %d/%d" %
                (countDoneFiles, len(fileList)), 1)

    db_helper.commit(conn)
    db_helper.close()
    log('Successfully finished indexing files in: file://%s ....'
        % basePath, 5)


def tests():
    print("tests")


if __name__ == '__main__':
    tests()
