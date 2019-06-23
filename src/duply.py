#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals


import os
import sys
import stat
import md5
import time

from utils.logger import log
from datetime import datetime


def normPath(pathSring):
    if pathSring is not None:
        return os.path.normpath(pathSring)
    else:
        return None


# Setup Dump Search
filesBySize = {}
duplicateSets = []
blockList = []

useBadFolders = True
useBadFiles = True
minSize = 2
stopDeepScanAt = 10000000  # stops the real scan at 10mb

walkerLastInfo = 0
walkerCountFiles = 0

duplyLastInfo = 0

automaticllyChooseShortestDir = False


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
                log('Skip file://%s because there is a Makefile file in it!' %
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
    global walkerLastInfo
    global walkerCountFiles
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

        # unimportend anyway
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
                log('Skip file://%s because it is a .metadata directory!'
                    % path, 0)
                continue

            walker(path)
            continue

        # add found file to fileBySize list
        size = os.stat(path)[stat.ST_SIZE]
        # print path + " size: " + str(size)
        if size < minSize:
            continue
        a = []
        if size in filesBySize:
            a = filesBySize[size]
        else:
            filesBySize[size] = a
        a.append(path)
        walkerCountFiles += 1

    if time.time() - walkerLastInfo >= 5:
        walkerLastInfo = time.time()
        log(datetime.now().strftime('%H:%M:%S') + " Still scanning for files"
            + " in the path... %d files found" % walkerCountFiles, 5)


def listDir(dirname):
    if not os.path.isdir(dirname):
        return
    fnames = os.listdir(dirname)

    for f in fnames:
        path = os.path.join(dirname, f)
        if os.path.isdir(path):
            log("Dir: " + f, 4)

        if os.path.isfile(path):
            if isFileInDupes(path):
                log("File: " + f, 3)
            else:
                log("File: " + f, 5)


def listDirs(fnames):
    for i, f in enumerate(fnames):
        dirname = os.path.dirname(f)
        log("[" + str(i) + "] file://" + dirname, 2)
        listDir(dirname)


def isFileInDupes(path):
    global duplicateSets
    for d in duplicateSets:
        for f in d:
            if f == path:
                return True
    return False


stepcounter = 0
countDeletedFiles = 0
countDeletedEmptyFolder = 0


def getemptyfiles(rootdir):
    global countDeletedFiles
    for root, dirs, files in os.walk(rootdir):
        for d in ['RECYCLER', 'RECYCLED']:
            if d in dirs:
                dirs.remove(d)

        for f in files:
            fullname = os.path.join(root, f)
            try:
                if os.path.getsize(fullname) == 0:
                    log('Deleting file://%s' % fullname, 2)
                    try:
                        os.remove(fullname)
                        countDeletedFiles += 1
                    except OSError:
                        nothere = True
            except WindowsError:
                continue


def searchfordumps(first_path, second_path):
    # find dublication in folder  pathtoSearch
    global filesBySize
    global walkerLastInfo
    global walkerCountFiles
    global duplyLastInfo

    # Ask automisation question(s) at start, so user can chill after that
    askForAutomisation()

    filesBySize = {}
    log('Scanning in first path for files: file://%s ....' % first_path, 0)

    walkerCountFiles = 0
    walkerLastInfo = time.time()
    walker(first_path)
    log("Finished, %d files found!\n" % walkerCountFiles, 5)

    if second_path is not None:
        log('Scanning in second path for files: file://%s ....' % second_path, 0)

        walkerCountFiles = 0
        walkerLastInfo = time.time()
        walker(second_path)
        log("Finished, %d files found!\n" % walkerCountFiles, 5)

    log('Search for potential duplicates...', 0)
    duplyLastInfo = time.time()
    # Create simple Hash list of first 1024 byte
    potentialDuplicates = []  # 2D Array (List of outFiles Array)
    potentialCount = 0  # List of files -  not sets
    trueType = type(True)
    sizes = filesBySize.keys()
    sizes.sort()
    for k in sizes:
        inFiles = filesBySize[k]
        hashOutFiles = {}  # dictionary - hash to array of filenames
        hashes = {}   # Hash Directory
        if len(inFiles) is 1:
            continue

        # log('Testing %d files of size %d...' % (len(inFiles), k), 0)
        for fileName in inFiles:
            if not os.path.isfile(fileName):
                continue
            aFile = file(fileName, 'r')
            hasher = md5.new(aFile.read(1024))
            hashValue = hasher.digest()
            if hashValue in hashes:
                if hashValue not in hashOutFiles:
                    hashOutFiles[hashValue] = []
                    hashOutFiles[hashValue].append(hashes[hashValue])
                hashOutFiles[hashValue].append(fileName)
            else:
                hashes[hashValue] = fileName

            aFile.close()
        for hash in hashOutFiles:
            if len(hashOutFiles[hash]):
                potentialDuplicates.append(hashOutFiles[hash])
                potentialCount = potentialCount + len(hashOutFiles[hash])

        if time.time() - duplyLastInfo >= 5:
            duplyLastInfo = time.time()
            log((datetime.now().strftime('%H:%M:%S') + " Still simple"
                 + " comparing files in the path... %d potential duplicate sets"
                 + " found") % len(potentialDuplicates), 5)
    del filesBySize

    log('%d files found that could potentially be duplicates. In %d sets...' %
        (potentialCount, len(potentialDuplicates)), 0)
    log('Scanning for real duplicates...\n', 0)

    global duplicateSets
    duplyLastInfo = time.time()
    duplicateSets = []  # 2D Array of real duplicates
    countDoneSets = 0
    for aSet in potentialDuplicates:
        countDoneSets += 1
        hashOutFiles = {}  # dictionary - hash to array of filenames
        hashes = {}
        for fileName in aSet:
            # log('Scanning file "%s"...' % fileName, 0)
            aFile = file(fileName, 'r')
            hasher = md5.new()
            countHashedBlocks = 0
            while True:
                r = aFile.read(4096)
                if not len(r):
                    break
                hasher.update(r)
                countHashedBlocks += 1
                if countHashedBlocks * 4096 >= stopDeepScanAt:
                    # don't read complete file
                    break
            aFile.close()
            hashValue = hasher.digest()
            if hashValue in hashes:
                if hashValue not in hashOutFiles:
                    hashOutFiles[hashValue] = []
                    hashOutFiles[hashValue].append(hashes[hashValue])
                hashOutFiles[hashValue].append(fileName)
            else:
                hashes[hashValue] = fileName
        for hash in hashOutFiles:
            if len(hashOutFiles[hash]):
                duplicateSets.append(hashOutFiles[hash])
        if time.time() - duplyLastInfo >= 5:
            duplyLastInfo = time.time()
            log(datetime.now().strftime('%H:%M:%S') + " Still real comparing"
                + " files in the path... %d duplicates found, %d sets checked" %
                (len(duplicateSets), countDoneSets), 5)

    stepsToDo = len(duplicateSets)

    log('%d real duplicate sets found.' % len(duplicateSets), 1)

    log('You have to make ' + str(stepsToDo) + " decisions now. Have fun!", 1)

    global countDeletedFiles
    global countDeletedEmptyFolder
    global stepcounter
    stepcounter = 0

    countDeletedFiles = 0
    countDeletedEmptyFolder = 0

    if second_path is not None:
        automerge()

    if automaticllyChooseShortestDir is False:
        for d in list(duplicateSets):
            choice = getChoise(d)
            if choice < len(d) and choice >= 0:
                log('Your choice is %s' %
                    "[" + str(choice) + "] file://" + d[choice] + " ", 1)

                for i, f in enumerate(d):
                    if not i == choice:
                        log('Deleting file://%s' % f, 2)
                        try:
                            os.remove(f)
                            countDeletedFiles += 1
                        except Exception:
                            notthere = True

                        try:
                            emptyDir = os.path.dirname(f)
                            os.rmdir(emptyDir)
                            countDeletedEmptyFolder += 1
                            log('Deleting empty dir file://%s' % emptyDir, 2)
                        except OSError:
                            empty = False
                            duplicateSets.remove(d)
            elif choice == -1:
                log('Skip file://%s' % d[0], 0)
            elif choice == -2:
                log('Directory option finished', 0)
            elif choice == -3:
                log('file://%s already processed' % d[0], 0)

            stepcounter += 1
            log(str(stepcounter) + ' done of ' + str(stepsToDo), 1)
    else:
        for d in list(duplicateSets):
            automaticallyChooseDir(d)
            log('Directory option finished', 0)
            stepcounter += 1
            log(str(stepcounter) + ' done of ' + str(stepsToDo), 1)

    # Delete empty files
    if second_path is not None:
        getemptyfiles(second_path)

    getemptyfiles(first_path)
    deleteEmptyFolders()

    log("Stats:\n"
        + "%d files have been deleted\n" % countDeletedFiles
        + "%d empty folders have been deleted\n" % countDeletedEmptyFolder
        + "%d remaining duplicate sets\n" % len(duplicateSets), 1)

    log("It's done. Thanks for using Dubly.", 1)


def askForAutomisation():
    global automaticllyChooseShortestDir

    Join = raw_input(
        'Do you want to automatically delete all'
        + ' duplicates and keep the orignial file with the shortest path'
        + ' (the directory option is choosen, so it minimize the directories,'
        + ' but it could be that for some files the path is not minimized)?'
        + ' [y/N]\n')

    while Join not in ['', 'no', 'No', 'n', 'N', 'yes', 'Yes', 'y', 'Y']:
        Join = raw_input('I didn\'t understand you, what do you mean? [y/N]')

    if Join == '':
        return

    if Join in ['yes', 'Yes', 'y', 'Y']:
        automaticllyChooseShortestDir = True


def automerge():
    global duplicateSets
    global countDeletedFiles
    global countDeletedEmptyFolder
    global stepcounter

    Join = raw_input(
        'Do you want to automatically delete from the second folder all' +
        ' duplicates that already exist in the first folder? [y/N]\n')

    while Join not in ['', 'no', 'No', 'n', 'N', 'yes', 'Yes', 'y', 'Y']:
        Join = raw_input('I didn\'t understand you, what do you mean? [y/N]')

    if Join not in ['yes', 'Yes', 'y', 'Y']:
        return

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
                    try:
                        os.remove(filePath)
                        countDeletedFiles += 1
                    except OSError:
                        nothtere = True

                    stepcounter += 1
                    try:
                        emptyDir = os.path.dirname(filePath)
                        os.rmdir(emptyDir)
                        log('Deleting empty dir file://%s' % emptyDir, 2)
                        countDeletedEmptyFolder += 1
                    except OSError:
                        empty = False
            duplicateSets.remove(duplicateSet)


def deleteEmptyFolders():
    global countDeletedEmptyFolder
    # Delete empty folders
    folders = list(os.walk(first_path, topdown=False))[:-1]
    for folder in folders:
        if not folder[2]:
            try:
                os.rmdir(folder[0])
                log('Deleting empty dir file://%s' % folder[0], 2)
                countDeletedEmptyFolder += 1
            except OSError:
                empty = False

    # second path
    if second_path is not None:
        folders = list(os.walk(second_path, topdown=False))[:-1]
        for folder in folders:
            if not folder[2]:
                try:
                    os.rmdir(folder[0])
                    log('Deleting empty dir file://%s' % folder[0], 2)
                    countDeletedEmptyFolder += 1
                except OSError:
                    empty = False


def getChoise(dupe):
    global blockList
    global skipLog
    global duplicateSets

    done = False
    while not done:
        done = True

        usr_input = "-1"

        while int(usr_input) not in range(0, len(dupe)):
            log("\n\n\nWhich of the following files do you want to keep:", 4)

            for i, d in enumerate(dupe):
                log("[" + str(i) + "] file://" + d + "", 5)

            log("[s] Skip file 0", 5)
            log("[l] List directories", 5)
            log("[d] Directory options", 5)

            usr_input = "-1"

            usr_input = str(raw_input("Input: "))
            if usr_input == "s":
                # log('Skip file://%s' % dupe[0], 2)
                skipLogWriter = open(skipLogPath, 'a')
                skipLogWriter.write(datetime.now().strftime(
                    '%d.%m.%Y %H:%M:%S') + " " + dupe[0] + "\n")
                skipLogWriter.close()

                skipLogReader = open(skipLogPath, 'r')
                skipLog = skipLogReader.read()
                skipLogReader.close()

                duplicateSets.remove(dupe)

                usr_input = "-1"
                break

            elif usr_input == "l":
                usr_input = "-1"
                listDirs(dupe)
            elif usr_input == "d":
                usr_input = "-1"
                wahl2 = getChoiseDir(dupe)

                if wahl2 == 1:  # directory option correct
                    usr_input = "-2"
                    break
                elif wahl2 == 0:  # back to file option
                    done = False
                    break
            elif usr_input == "ds":
                skipDirname = os.path.dirname(dupe[0])
                skipAllFilesIn(skipDirname)
                usr_input = "-2"
                break
            elif not usr_input.isdigit():
                usr_input = "-1"

    return int(usr_input)


def getChoiseDir(dupe):
    usr_input = "-1"

    while int(usr_input) not in range(0, len(dupe)):
        log("\nWhich of the following directories should be kept:", 4)
        for i, f in enumerate(dupe):
            dirname = os.path.dirname(f)
            log("[" + str(i) + "] file://" + dirname, 2)

        log("[l] List directoys", 5)
        log("[s] Skip all files in directory 0", 5)
        log("[f] File options", 5)

        usr_input = "-1"

        usr_input = str(raw_input("Input: "))

        if usr_input == "l":
            usr_input = "-1"
            listDirs(dupe)

        elif usr_input == "s":
            usr_input = "-1"
            # skip all files in folder 0
            skipDirname = os.path.dirname(dupe[0])
            skipAllFilesIn(skipDirname)
            return 1

        elif usr_input == "f":
            usr_input = "-1"
            return 0
        elif not usr_input.isdigit():
            usr_input = "-1"

    # keep all files in selected folder
    # delete all files in other folders

    log('Your choice is %s' % "[" + usr_input + "] file://" +
        os.path.dirname(dupe[int(usr_input)]) + " ", 1)
    keepDirname = os.path.dirname(dupe[int(usr_input)])
    keepAllFilesIn(keepDirname)

    return 1


def automaticallyChooseDir(dupe):

    log("\nAutomaticly decides between following directories:", 4)
    auto_input = 0
    lengthPath = len(os.path.dirname(enumerate(dupe)[0]))
    for i, f in enumerate(dupe):
        dirname = os.path.dirname(f)
        log("[" + str(i) + "] file://" + dirname, 2)
        if lengthPath < len(dirname):
            auto_input = i

    # keep all files in selected folder
    # delete all files in other folders

    log('Automaitc choice is %s' % "[" + auto_input + "] file://" +
        os.path.dirname(dupe[int(auto_input)]) + " ", 1)
    keepDirname = os.path.dirname(dupe[int(auto_input)])
    keepAllFilesIn(keepDirname)

    return 1


def keepAllFilesIn(dirname):
    # keep all Files in dirname and delete all duplicates

    global blockList
    # global stepcounter
    global countDeletedEmptyFolder
    global countDeletedFiles
    global duplicateSets
    killedFiles = 0
    for d in list(duplicateSets):
        # check if one file in d is in dirname
        choice = -1
        for i, f in enumerate(d):
            fdir = os.path.dirname(f)

            if fdir == dirname:
                log("[" + str(killedFiles) + '] Original file://%s' % f, 4)
                choice = i
                killedFiles += 1
                break

        if not choice == -1:

            for i, f in enumerate(d):
                if not i == choice:
                    log('Deleting file://%s' % f, 2)
                    try:
                        os.remove(f)
                        countDeletedFiles += 1
                    except OSError:
                        notthere = True

                    try:
                        emptyDir = os.path.dirname(f)
                        os.rmdir(emptyDir)
                        countDeletedEmptyFolder += 1
                        log('Deleting empty dir file://%s' % emptyDir, 2)
                    except OSError:
                        empty = False
            duplicateSets.remove(d)

    # need to add folders to block list

    blockList.append(dirname)


def skipAllFilesIn(dirname):
    # skip all Files in dirname

    global blockList
    global duplicateSets
    skipedFiles = 0
    for d in list(duplicateSets):
        # check if one file in d is in dirname
        for i, f in enumerate(d):
            fdir = os.path.dirname(f)

            if fdir == dirname:
                log("[" + str(skipedFiles) + '] Skip file://%s' % f, 0)
                skipLogWriter = open(skipLogPath, 'a')
                skipLogWriter.write(datetime.now().strftime(
                    '%d.%m.%Y %H:%M:%S') + " " + f + "\n")
                skipLogWriter.close()

                global skipLog
                skipLogReader = open(skipLogPath, 'r')
                skipLog = skipLogReader.read()
                skipLogReader.close()
                skipedFiles += 1

                duplicateSets.remove(d)

                break

    # need to add folders to block list
    blockList.append(dirname)


log('Dubly started working.', 1)


if not len(sys.argv) == 2 and not len(sys.argv) == 3:
    log("Dubly is easy to use.\n"
        + "Please read the following information in detail.\n"
        + "It is possible to start Dubly with one or two parameters.\n"
        + "The first parameter should be a path to a folder from which nothing"
        + " should be deleted automatically.\n"
        + "The second parameter should be a path from which all duplicates"
        + " that already exist in the first specified path are automatically"
        + " deleted. The paths must be different and must not be subfolders of"
        + " each other.")
    exit(1)


# first path
first_path = str(sys.argv[1])

if not os.path.isdir(first_path):
    log("Error parsing Variable. First argument should be a valid path.", 3)
    exit()

first_path = os.path.abspath(first_path)

if not os.path.isdir(first_path):
    log("Error parsing Variable. Absolute path of first path should be valid"
        + " too. Calculated absolute path: " + first_path, 3)
    exit()

log("First path found file://" + first_path, 5)

second_path = None

if len(sys.argv) == 3:
    # second path
    second_path = str(sys.argv[2])

    if not os.path.isdir(second_path):
        log("Error parsing Variable. Second argument should be a valid path.",
            4)
        exit()

        second_path = os.path.abspath(second_path)

    if not os.path.isdir(second_path):
        log("Error parsing Variable. Absolute path of second path should be"
            + " valid too. Calculated absolute path: " + second_path, 3)
        exit()

    log("Second path found file://" + second_path, 5)

    if (normPath(first_path) + "/" in second_path
        or normPath(second_path) + "/" in first_path
            or normPath(first_path) == normPath(second_path)):
        log("Error parsing Variable. Both paths must be independent of each"
            + " other.", 3)
        exit()

skipLogPath = normPath(os.path.join(first_path, ".skiphistory.log"))


# create skipFile
if not os.path.isfile(skipLogPath):
    skipLogWriter = open(skipLogPath, 'a')
    skipLogWriter.write("SkipFile:V1.0")
    skipLogWriter.close()
    log("Created skip file: file://" + skipLogPath, 0)

log("Using history file: file://" + skipLogPath, 0)

skipLogReader = open(skipLogPath, 'r')
skipLog = skipLogReader.read()
skipLogReader.close()


searchfordumps(normPath(first_path), normPath(second_path))


log("Dubly Complete", 1)
