#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#  Copyright 2017 Daniel Vogt



import cookielib
import urllib2
import urllib
import io
import os
import os.path
import hashlib
import sys
import stat
import md5
import re
import filecmp
import sys
import cgi
import fnmatch
import datetime as dt

from datetime import datetime
from ConfigParser import ConfigParser
from urlparse import urlparse


import gi
gi.require_version('Notify', '0.7') 
from gi.repository import Notify

Notify.init("Duby")

#logvariable
useColors = "true"


#Import Libs if needed
try:
   from bs4 import BeautifulSoup
except Exception as e:
   print("Module BeautifulSoup4 is missing!")
   exit(1)


#add colors
if useColors == "true":
   try:
      from colorama import init
   except Exception as e:
      print("Module Colorama is missing!")
      exit(1)
   
   try:
      from termcolor import colored
   except Exception as e:
      print("Module Termcolor is missing!")
      exit(1)

   # use Colorama to make Termcolor work on Windows too
   init()


   
#utf8 shit
reload(sys)
sys.setdefaultencoding('utf-8')



#Log levels:

#1 = grün
#2 = gelb
#3 = rot
#4 = violet
#5 = blau


 
def log(logString, level=0):
   logString = logString.encode('utf-8')
   if useColors == "true":
      if level == 0:
         print(datetime.now().strftime('%H:%M:%S') + " " + logString)
      elif level == 1:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "green"))
      elif level == 2:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "yellow"))
      elif level == 3:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "red"))
      elif level == 4:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "magenta"))
      elif level >= 5:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "cyan"))
   else:
      print(datetime.now().strftime('%H:%M:%S') + " " + logString)



def checkQuotationMarks(settingString):
   if not settingString is None and settingString[0] == "\"" and settingString[-1] == "\"":
      settingString = settingString[1:-1]
   if settingString is None:
      settingString = ""
   return settingString


def addSlashIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "/":
      settingString = settingString + "/"
   return settingString


def addQuestionmarkIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "?":
      settingString = settingString + "?"
   return settingString


def normPath(pathSring):
   return os.path.normpath(pathSring)



def removeSpaces(pathString):
   return pathString.replace(" ", "")




def checkBool(variable, name):
   if variable == "true" or variable == "false":
      return
   else:
      log("Error parsing Variable. Please check the config file for variable: " + name + ". This variable should be 'true' or 'false'", 3)
      exit()


def checkInt(variable, name):
   if variable.isdigit():
      return
   else:
      log("Error parsing Variable. Please check the config file for variable: " + name + ". This variable should be an integer", 3)
      exit()



def progress(count, total, suffix=''):
    bar_len = 30
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%% ...%s\r' % (bar, percents, suffix))
    sys.stdout.flush()


def checkConf(cat, name):
  global conf
  try: 
     return checkQuotationMarks(conf.get(cat, name))
  except Exception as e:
     log("Variable in config is missing. Please set the variable: " + name + " in the config file in section: " + cat, 3)
     exit()  


#get Config
#conf = ConfigParser()
#project_dir = os.path.dirname(os.path.abspath(__file__))
#conf.read(os.path.join(project_dir, 'config.ini'))


 
def printNL(anz):
   for i in range(anz):
      print ""

    


#Setup Dump Search    
filesBySize = {}
dupes = []
blockList = []

def isBadFolder(fnames, dirname):
   for f in fnames:
      path = os.path.join(dirname, f)
      if os.path.isfile(path):
         #skip file .project
         if f == ".project":
            log('Skip file://%s because there is a .project file in it!' % dirname, 0)
            return True
         
         if f == "Makefile" or f == "MAKEFILE":
            log('Skip file://%s because there is a Mekfile file in it!' % dirname, 0)
            return True
         
      elif os.path.isdir(path):
         #skip subfolder .idea
         if f == ".idea":
            log('Skip file://%s because there is a .idea directory in it!' % dirname, 0)
            return True
   return False


def walker(dirname):
   fnames = os.listdir(dirname)
   
   if isBadFolder(fnames, dirname) == True:
      return


   global filesBySize
   
   try:
      fnames.remove('Thumbs')
   except ValueError:
      pass
   
   for f in fnames:
      path = os.path.join(dirname, f)
      #if f.endswith(("~", ".aux", ".log", ".dvi", ".lof", ".lot",
      # ".bit", ".idx", ".glo", ".bbl", ".bcf", ".ilg", ".toc",
      #  ".ind", ".out", ".blg", ".fdb", ".latexmk", ".fls",
      #   ".o", ".del", ".index", ".mf", ".properties",
      #   ".zzz", ".mcu8051ide", "LICENSE")):
      #      log('Skip file://%s because it is on the blacklist!' % path, 0)
      #      continue

      #if f.startswith((".", "~")):
      #      log('Skip file://%s because it is on the blacklist!' % path, 0)
      #      continue
        
      #walk in dir
      if os.path.isdir(path) and not os.path.islink(path):
         #dont mess with git
         if f == ".git":
            log('Skip file://%s because it is a .git directory!' % path, 0)
            continue
         #if f == "out":
         #   log('Skip file://%s because it is a out directory!' % path, 0)
         #   continue
         #if f == ".metadata":
         #   log('Skip file://%s because it is a .metadata directory!' % path, 0)
         #   continue
            

         #dont mess with git

         walker(path)
         continue
   
         
      size = os.stat(path)[stat.ST_SIZE]
      #print path + " size: " + str(size)
      if size < 2:
         continue
      if filesBySize.has_key(size):
         a = filesBySize[size]
      else:
         a = []
         filesBySize[size] = a
      a.append(path)

   
def listDir(dirname):
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
   global dupes
   for d in dupes:
      for f in d:
         if f == path:
            return True
   return False


stepcounter = 0
   
def decodeFilename(fileName):

  htmlDecode = urllib.unquote(fileName).decode('utf8')
  htmlDecode = htmlDecode.replace('/', '-').replace('\\', '-').replace(' ', '-').replace('#', '-').replace('%', '-').replace('&', '-').replace('{', '-').replace('}', '-').replace('<', '-')
  htmlDecode = htmlDecode.replace('>', '-').replace('*', '-').replace('?', '-').replace('$', '-').replace('!', '-').replace(u'‘', '-').replace('|', '-').replace('=', '-').replace(u'`', '-').replace('+', '-')
  htmlDecode = htmlDecode.replace(':', '-').replace('@', '-').replace('"', '-')
  old = urllib.unquote(fileName).decode('utf8')
  if(old != htmlDecode):
  	log("Changed filename from '" + old + "'' to '" + htmlDecode + "'", 0)

  return htmlDecode
 




def searchfordumps(pathtoSearch):
    #find dublication in folder  pathtoSearch
    global filesBySize
    filesBySize = {}
    log('Scanning directory file://%s ....' % pathtoSearch, 0)
    printNL(1)
    walker(pathtoSearch)
    printNL(1)
    
    log('Finding potential duplicates...', 0)
    potentialDupes = []
    potentialCount = 0
    trueType = type(True)
    sizes = filesBySize.keys()
    sizes.sort()
    for k in sizes:
        inFiles = filesBySize[k]
        outFiles = []
        hashes = {}
        if len(inFiles) is 1:
          continue

        #log('Testing %d files of size %d...' % (len(inFiles), k), 0)
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
                    hashes[hashValue] = True
                outFiles.append(fileName)
            else:
                hashes[hashValue] = fileName
            aFile.close()
        if len(outFiles):
            potentialDupes.append(outFiles)
            potentialCount = potentialCount + len(outFiles)
    del filesBySize

    log('Found %d sets of potential duplicates...' % potentialCount, 0)
    log('Scanning for real duplicate...', 0)

    global dupes
    dupes = []
    for aSet in potentialDupes:
        outFiles = []
        hashes = {}
        for fileName in aSet:
            #log('Scanning file "%s"...' % fileName, 0)
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
                if not len(outFiles):
                    outFiles.append(hashes[hashValue])
                outFiles.append(fileName)
            else:
                hashes[hashValue] = fileName
        if len(outFiles):
            dupes.append(outFiles)


   
    stepsToDo = len(dupes)
    printNL(5)
    
    log('You have to make now ' + str(stepsToDo) + " decisions. Have fun!", 1)
    global stepcounter
    stepcounter = 0
    
    for d in list(dupes): 
      isshit = False
      for f in d:
        if not pref_directory in f:
          isshit = True
          break

      if isshit: 
        for f in d:
           if pref_directory in f:
              log('Deleting file://%s' % f, 2)
              os.remove(f)
              try:
                 emptyDir = os.path.dirname(f)
                 os.rmdir(emptyDir)
                 log('Deleting empty dir file://%s' % emptyDir, 2)
              except OSError:
                 empty = False

      dupes.remove(d)

      stepcounter += 1
      log(str(stepcounter) + ' done of ' + str(stepsToDo), 1)


   



log("Dubly started working.", 1)


#1 = grün
#2 = gelb
#3 = rot
#4 = violet
#5 = blau

if not len(sys.argv) == 3 :
    log("Error parsing Variable. First Argument should be a path, in which I will check for dublicates. Second Argument should be a path, in which I will annihilate all dublicates.", 3)
    exit()

root_directory = str(sys.argv[1])
pref_directory = str(sys.argv[2])
if not os.path.isdir(pref_directory):
  log("Error parsing Variable. Second Argument should be a valid path.", 3)
  exit()

pref_directory = os.path.abspath(pref_directory)


if not os.path.isdir(root_directory):
  log("Error parsing Variable. Absolut Path should be valid too. Caluclated absulut path: " + pref_directory, 3)
  exit()
   
log("root_directory found file://" + root_directory, 0)


#check variables:
if not os.path.isdir(root_directory):
    log("Error parsing Variable. First Argument should be a valid path.", 3)
    exit()
    
root_directory = os.path.abspath(root_directory)

if not os.path.isdir(root_directory):
    log("Error parsing Variable. Absolut Path should be valid too. Caluclated absulut path: " + root_directory, 3)
    exit()
   
log("root_directory found file://" + root_directory, 0)

if not root_directory in pref_directory:
    log("Error parsing Variable. Second Argunment need to be a subfolder of the first Argument.", 3)
    exit()


dubLogPath = normPath(addSlashIfNeeded(root_directory)+ ".dublyhistory.log")
skipLogPath = normPath(addSlashIfNeeded(root_directory)+ ".skiphistory.log")



 #create logFile
if not os.path.isfile(dubLogPath):
   dubLogWriter = open(dubLogPath, 'ab')
   dubLogWriter.write("LogFile:V1.0")
   dubLogWriter.close()
   log("Created history file: file://" + dubLogPath, 0)

log("Using history file: file://" + dubLogPath, 0)

 #create skipFile
if not os.path.isfile(skipLogPath):
   skipLogWriter = open(skipLogPath, 'ab')
   skipLogWriter.write("SkipFile:V1.0")
   skipLogWriter.close()
   log("Created skip file: file://" + skipLogPath, 0)

log("Using history file: file://" + skipLogPath, 0)
   
log('I will store information about all your decisions in the file://' + dubLogPath + ' and  file://' + skipLogPath + ' file.', 4)


dubLogReader = open(dubLogPath, 'rb')
dubLog = dubLogReader.read()
dubLogReader.close()

skipLogReader = open(skipLogPath, 'rb')
skipLog = skipLogReader.read()
skipLogReader.close()



searchfordumps(normPath(root_directory))


log("Dubly Complete", 1)
