#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals

import os
import stat
import time

from logger import log


def isCriticalFolder(fileList, rootPath):
    """
    Check if the directory is a critical directory
    by checking if there are any special files
    :param fileList: the file list within the directory
    :param rootPath: the path to the directory
    :return: True if it is a critical directory else False
    """

    for file in fileList:
        path = os.path.join(rootPath, file)
        if os.path.isfile(path):
            # skip folders with .project files
            if file == ".project":
                log('Skip file://%s because there is a .project file in it!' %
                    rootPath, 0)
                return True
            # skip folders with MAKEFILEs
            if file == "Makefile" or file == "MAKEFILE":
                log('Skip file://%s because there is a Makefile file in it!' %
                    rootPath, 0)
                return True

        elif os.path.isdir(path):
            # skip folders with .idea subfolder
            if file == ".idea":
                log('Skip file://%s because there is a .idea directory'
                    + ' in it!' % rootPath, 0)
                return True
    return False


def isCriticalFolderName(folderName):
    """
    Check if the directory is a critical directory
    by checking if the name matchs a critical one
    :param folderName: the name of a directory
    :return: True if it is a critical directory else False
    """
    # dont mess with git and other important folders
    if folderName in [".git", "out", ".metadata", "Thumbs"]:
        return True
    return False


def isCriticalFileName(fileName):
    """
    Check if the file is a critical file
    by checking if the name matchs a critical one
    :param fileName: the name of a file
    :return: True if it is a critical file else False
    """

    if fileName.endswith(("~", ".aux", ".log", ".dvi", ".lof",
                          ".lot", ".bit", ".idx", ".glo", ".bbl",
                          ".bcf", ".ilg", ".toc", ".ind", ".out",
                          ".blg", ".fdb", ".latexmk", ".fls",
                          ".o", ".del", ".index", ".mf",
                          ".properties", ".zzz", ".mcu8051ide",
                          "LICENSE")):
        return True

    if fileName.startswith((".", "~")):
        return True

    return False


def normPath(pathSring):
    if pathSring is not None:
        return os.path.normpath(pathSring)
    else:
        return None


def get_list_of_files_in(basePath, rootPath="", ignoreCriticalFolders=False,
                         ignoreCriticalFiles=False, lastInfoTime=0):
    """
    Generates a list of files inside a directory
    including filesize and modified_date
    :param basePath: the Path to the base directory
    (normaly where the database file is)
    :param rootPath: the Path used for recrusive search
    :param ignoreCriticalFolders: if critical folders should be ignored
    :param ignoreCriticalFiles: if critical files should be ignored
    :return: a tuple (list of files , lastInfoTime)
    lastInfoTime is only for output purpose
    """
    actualPath = os.path.join(basePath, rootPath)
    fileList = os.listdir(actualPath)

    resultFileList = []

    if ignoreCriticalFolders and isCriticalFolder(fileList, rootPath):
        return (resultFileList, lastInfoTime)

    for fileName in fileList:
        path = os.path.join(rootPath, fileName)
        fullPath = os.path.join(basePath, path)

        if ignoreCriticalFiles and os.path.isfile(fullPath) and isCriticalFileName(fileName):
            log('Skip file://%s because it is on the blacklist!' % fullPath, 0)
            continue

        # walk in dir
        if os.path.isdir(fullPath) and not os.path.islink(fullPath):
            # dont mess with git and other important folders
            if ignoreCriticalFolders and isCriticalFolderName(fileName):
                log('Skip file://%s because it is a %s directory!' %
                    (fullPath, fileName), 0)

            resultRecrusion = get_list_of_files_in(
                basePath, path, ignoreCriticalFolders, ignoreCriticalFiles, lastInfoTime)
            resultFileList += resultRecrusion[0]
            lastInfoTime = resultRecrusion[1]
            continue

        # add found file to fileBySize list
        statbuf = os.stat(fullPath)
        size = statbuf[stat.ST_SIZE]
        lastModified = statbuf[stat.ST_MTIME]
        resultFileList.append({
            "path": path,
            "size": size,
            "modified_date": lastModified
        })

    if time.time() - lastInfoTime >= 5:
        lastInfoTime = time.time()
        log("Still scanning for files in the path... %d files found" %
            len(resultFileList), 1)

    return (resultFileList, lastInfoTime)


def tests():
    resultScan = get_list_of_files_in(normPath(
        "/home/daniel/Desktop/other_repos/Duply"))
    print(resultScan[0])
    print(len(resultScan[0]))


if __name__ == '__main__':
    tests()
