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


 

    


#Setup Dump Search    
filesBySize = {}



def walker(arg, dirname, fnames):
    d = os.getcwd()
    os.chdir(dirname)
    global filesBySize

    try:
        fnames.remove('Thumbs')
    except ValueError:
        pass
    for f in fnames:
        if not os.path.isfile(f):
            continue
        size = os.stat(f)[stat.ST_SIZE]
        #print f + " size: " + str(size)
        if size < 100:
            continue
        if filesBySize.has_key(size):
            a = filesBySize[size]
        else:
            a = []
            filesBySize[size] = a
        a.append(os.path.join(dirname, f))
    os.chdir(d)





   
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
    os.path.walk(pathtoSearch, walker, filesBySize)

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

        log('Testing %d files of size %d...' % (len(inFiles), k), 0)
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

    for d in dupes:
       choice = getChoise(d)
       
       log('Your choise is %s' % "[" + str(choice) + "] file://" +d[choice] + " ", 1)
       
       logDuplicates(d, choice)
       for i, f in enumerate(d):
          if not i == choice:
             log('Deleting file://%s' % f, 2)
             os.remove(f)
             try:
                emptyDir = os.path.dirname(f)
                os.rmdir(emptyDir)
                log('Deleting empty dir file://%s' % emptyDir, 2)
             except OSError:
                empty = False




#log Duplicates
def logDuplicates(dupe, choice):
   dubLogWriter = io.open(dubLogPath, 'ab')

   
   dubLogWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "  Your choise was "+ str(choice) + " [ file://" + dupe[choice] + " ] I found that file on following places: ")
   
   for i, d in enumerate(dupe):
      if not i == choice and not i == len(dupe) - 1:
         dubLogWriter.write("file://" + d + " , ")
      elif not i == choice and i == len(dupe) - 1:
         dubLogWriter.write("file://" + d + "\n")
         

   dubLogWriter.close()

   
def getChoise(dupe):
   log("Make a decisson for the following files:", 4)
   
   for i, d in enumerate(dupe):
     log("[" + str(i) + "] file://" + d + "", 5)

   usr_input = '-1'
   while int(usr_input) not in range(0, len(dupe)):
      usr_input = input("Input: ")

   return int(usr_input)



      
log("Dubly started working.", 1)


#1 = grün
#2 = gelb
#3 = rot
#4 = violet
#5 = blau

root_directory = str(sys.argv[1])


#check variables:
if not os.path.isdir(root_directory):
    log("Error parsing Variable. First Argument should be a valid path.", 0)
    exit()
    
root_directory = os.path.abspath(root_directory)

if not os.path.isdir(root_directory):
    log("Error parsing Variable. Absolut Path should be valid too. Caluclated absulut path: " + root_directory, 0)
    exit()
   
log("root_directory found file://" + root_directory, 0)



dubLogPath = normPath(addSlashIfNeeded(root_directory)+ ".dublyhistory.log")


 #create crealHistoryfile
if not os.path.isfile(dubLogPath):
   dubLogWriter = open(dubLogPath, 'ab')
   dubLogWriter.write("LogFile:V1.0")
   dubLogWriter.close()
   log("Created history file: file://" + dubLogPath, 0)

   
log("Using history file: file://" + dubLogPath, 0)
log('I will store information about all your decisions in the file://' + dubLogPath + ' file.', 4)

dubLogReader = open(dubLogPath, 'rb')
dubLog = dubLogReader.read()
dubLogReader.close()


searchfordumps(normPath(root_directory))


log("Dubly Complete", 1)
