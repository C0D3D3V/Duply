#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#  Copyright 2017 Daniel Vogt
import urllib
import os
import os.path
import sys
import stat
import md5

from datetime import datetime

# utf8 shit
reload(sys)
sys.setdefaultencoding('utf-8')


def normPath(pathSring):
    return os.path.normpath(pathSring)


def printNL(anz):
    for i in range(anz):
        print("")


def log(logString, level=0):
    logString = logString.encode('utf-8')
    print(datetime.now().strftime('%H:%M:%S') + " " + logString)


# All found Files
filesBySize = {}

useBadFolders = False
useBadFiles = False
minSize = 2


def isBadFolder(fnames, dirname):
    for f in fnames:
        path = os.path.join(dirname, f)
        if os.path.isfile(path):
            # skip file .project
            if f == ".project":
                log('Skip file://%s because there is a .project file in it!' %
                    dirname, 0)
                return True

            if f == "Makefile" or f == "MAKEFILE":
                log('Skip file://%s because there is a Mekfile file in it!' %
                    dirname, 0)
                return True

        elif os.path.isdir(path):
            # skip subfolder .idea
            if f == ".idea":
                log('Skip file://%s because there is a .idea directory'
                    + ' in it!' % dirname, 0)
                return True
    return False


def walker(dirname):
    fnames = os.listdir(dirname)

    if useBadFolders and isBadFolder(fnames, dirname) is True:
        return

    global filesBySize

    # Nobody likes Thumbs folder
    try:
        fnames.remove('Thumbs')
    except ValueError:
        pass

    for f in fnames:
        path = os.path.join(dirname, f)

        # unimportant anyway
        if useBadFiles and f.endswith(("~", ".aux", ".log", ".dvi", ".lof",
                                       ".lot", ".bit", ".idx", ".glo", ".bbl",
                                       ".bcf", ".ilg", ".toc", ".ind", ".out",
                                       ".blg", ".fdb", ".latexmk", ".fls",
                                       ".o", ".del", ".index", ".mf",
                                       ".properties", ".zzz", ".mcu8051ide",
                                       "LICENSE")):
            log('Skip file://%s because it is on the blacklist!' % path, 0)
            continue

        if useBadFiles and f.startswith((".", "~")):
            log('Skip file://%s because it is on the blacklist!' % path, 0)
            continue

        # walk in dir
        if os.path.isdir(path) and not os.path.islink(path):
            # dont mess with git and other important folders
            if useBadFolders and f == ".git":
                log('Skip file://%s because it is a .git directory!' % path, 0)
                continue
            if useBadFolders and f == "out":
                log('Skip file://%s because it is a out directory!' % path, 0)
                continue
            if useBadFolders and f == ".metadata":
                log('Skip file://%s because it is a .metadata directory!' %
                    path, 0)
                continue

            walker(path)
            continue

        # add found file to fileBySize list
        size = os.stat(path)[stat.ST_SIZE]
        # print path + " size: " + str(size)
        if size < minSize:
            continue
        if filesBySize.has_key(size):
            a = filesBySize[size]
        else:
            a = []
            filesBySize[size] = a
        a.append(path)


def searchfordumps(first_path, second_path):
    # find dublication in folder  pathtoSearch
    global filesBySize
    filesBySize = {}
    log('Scanning in first path for files: file://%s ....' % first_path, 0)
    printNL(1)
    walker(first_path)

    log('Scanning in second path for files: file://%s ....' % second_path, 0)
    printNL(1)
    walker(second_path)

    printNL(1)

    log('Search for potential duplicates...', 0)

    # Create simple Hash list of first 1024 byte
    potentialDuplicates = []  # 2D Array (List of outFiles Array)
    potentialCount = 0  # List of files -  not sets
    trueType = type(True)
    sizes = filesBySize.keys()
    sizes.sort()
    for k in sizes:
        inFiles = filesBySize[k]
        outFiles = []
        hashes = {}  # Hash Dictionary
        if len(inFiles) is 1:
            continue

        # log('Testing %d files of size %d...' % (len(inFiles), k), 0)
        for fileName in inFiles:
            if not os.path.isfile(fileName):
                continue
            aFile = file(fileName, 'r')
            hasher = md5.new(aFile.read(1024))
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                x = hashes[hashValue]
                if type(x) is not trueType:
                    outFiles.append(hashes[hashValue])
                    hashes[hashValue] = True           # add first only ones
                outFiles.append(fileName)
            else:
                hashes[hashValue] = fileName
            aFile.close()
        if len(outFiles):
            potentialDuplicates.append(outFiles)
            potentialCount = potentialCount + len(outFiles)
    del filesBySize

    log('%d files found that could potentially be duplicates. In %d sets...' %
        (potentialCount, len(potentialDuplicates)), 0)
    log('Scanning for real duplicates...', 0)

    duplicateSets = []  # 2D Array of real duplicates
    for aSet in potentialDuplicates:
        hashOutFiles = {}  # dictionary - hash to array of filenames
        hashes = {}
        for fileName in aSet:
            # log('Scanning file "%s"...' % fileName, 0)
            aFile = file(fileName, 'r')
            hasher = md5.new()
            while True:
                r = aFile.read(4096)
                if not len(r):
                    break
                hasher.update(r)
            aFile.close()
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                if hashValue not in hashOutFiles:
                    hashOutFiles[hashValue] = []
                    hashOutFiles[hashValue].append(hashes[hashValue])
                hashOutFiles[hashValue].append(fileName)
            else:
                hashes[hashValue] = fileName
        for hash in hashOutFiles:
            if len(hashOutFiles[hash]):
                duplicateSets.append(hashOutFiles[hash])

    printNL(2)

    log('%d real duplicate sets found.' % len(duplicateSets), 1)

    countDeletedFiles = 0
    countDeletedEmptyFolder = 0

    for duplicateSet in list(duplicateSets):
        toDelete = False
        for filePath in duplicateSet:
            # Make sure that one duplicate is in first path
            if first_path in filePath:
                for file2Path in duplicateSet:
                    # Make sure that one duplicate is in second path
                    if second_path in file2Path:
                        toDelete = True
                        break
                break

        if toDelete:
            for filePath in duplicateSet:
                if second_path in filePath:
                    log('Deleting file://%s' % filePath, 2)
                    os.remove(filePath)
                    countDeletedFiles += 1
                    try:
                        emptyDir = os.path.dirname(filePath)
                        os.rmdir(emptyDir)
                        log('Deleting empty dir file://%s' % emptyDir, 2)
                        countDeletedEmptyFolder += 1
                    except OSError:
                        empty = False
            duplicateSets.remove(duplicateSet)

    # Delete empty folders
    folders = list(os.walk(second_path, topdown=False))[:-1]
    for folder in folders:
        if not folder[2]:
            try:
                os.rmdir(folder[0])
                log('Deleting empty dir file://%s' % folder[0], 2)
                countDeletedEmptyFolder += 1
            except OSError:
                empty = False

    log("Stats:\n"
        + "%d files have been deleted\n" % countDeletedFiles
        + "%d empty folders have been deleted\n" % countDeletedEmptyFolder
        + "%d remaining duplicate sets\n" % len(duplicateSets), 1)

    log("It's done. Thanks for using Automerge.", 1)


log("Automerge welcomes you!", 1)


if not len(sys.argv) == 3:
    log("Automerge is easy to use.\n"
        + "However, no warnings are issued before deleting files! Therefore, please read the following information in detail.\n"
        + "Two parameters are required.\n"
        + "The first parameter should be a path to a folder from which nothing should be deleted.\n"
        + "The second parameter should be a path from which all duplicates that already exist in the first specified path will be deleted. \n"
        + "The paths must be different and not subfolders of each other.")
    exit(1)


# first path
first_path = str(sys.argv[1])

if not os.path.isdir(first_path):
    log("Error parsing Variable. First argument should be a valid path.", 3)
    exit()

first_path = os.path.abspath(first_path)

if not os.path.isdir(first_path):
    log("Error parsing Variable. Absolut path of first path should be valid too. Calculated absulut path: " + first_path, 3)
    exit()

log("First path found file://" + first_path, 0)


# second path
second_path = str(sys.argv[2])

if not os.path.isdir(second_path):
    log("Error parsing Variable. Second argument should be a valid path.", 3)
    exit()

second_path = os.path.abspath(second_path)


if not os.path.isdir(second_path):
    log("Error parsing Variable. Absolut path of second path should be valid too. Calculated absulut path: " + second_path, 3)
    exit()

log("Second path found file://" + second_path, 0)

if (first_path in second_path or second_path in first_path
        or first_path == second_path):
    log("Error parsing Variable. Second Argunment need to be a subfolder of the first Argument.", 3)
    exit()


searchfordumps(normPath(first_path), normPath(second_path))


log("Dubly Complete", 1)
