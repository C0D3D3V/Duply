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

def isBadFolder(fnames, dirname):
   for f in fnames:
      path = os.path.join(dirname, f)
      if os.path.isfile(path):
         #skip file .project
         if f == ".project":
            log('Skip file://%s because there is a .project file in it!' % dirname, 0)
            return True
         
      elif os.path.isdir(path):
         #skip subfolder .idea
         if f == ".idea":
            log('Skip file://%s because there is a .idea folder in it!' % dirname, 0)
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
      #walk in dir
      if os.path.isdir(path):
         walker(path)
         continue
   
         
      size = os.stat(path)[stat.ST_SIZE]
      #print path + " size: " + str(size)
      if size < 100:
         continue
      if filesBySize.has_key(size):
         a = filesBySize[size]
      else:
         a = []
         filesBySize[size] = a
      a.append(path)

   
def listDir(dirname):
   fnames = os.listdir(dirname)
   
   
   log("Listening of: " + dirname, 2)
   for f in fnames:
      path = os.path.join(dirname, f)
      if os.path.isdir(path):
         log("Dir: " + f, 4)

      if os.path.isfile(path):
         log("File: " + f, 5)      





   
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
    walker(pathtoSearch)

    
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

            
    log('You have to make now ' + str(len(dupes)) + " decisions. Have fun!", 1)
    j = 0
    for d in dupes:
       choice = getChoise(d)
       if choice < len(d) and choice >= 0:
          log('Your choice is %s' % "[" + str(choice) + "] file://" +d[choice] + " ", 1)
          
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
       elif choice == len(d):
          log('Skip file://%s' % d[0], 2)
          skipLogWriter = open(skipLogPath, 'ab')
          skipLogWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " " + d[0] + "\n")
          skipLogWriter.close()
          
          global skipLog
          skipLogReader = open(skipLogPath, 'rb')
          skipLog = skipLogReader.read()
          skipLogReader.close()
       elif choice == -1:
          log('Skip file://%s' % d[0], 0)
       j += 1
       log(str(j) + ' done of ' + str(len(dupes)), 1)


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
   for f in dupe:
      if f in skipLog:
         return -1
         
   
   log("Which of the following files do you want to keep:", 4)
   
   for i, d in enumerate(dupe):
     log("[" + str(i) + "] " + d + "", 5)

   log("[" + str(len(dupe)) + "] Skip", 5)
   log("[" + str(len(dupe) + 1) + "] List dir", 5)
     
   usr_input = '-1'
   
   while int(usr_input) not in range(0, len(dupe) + 1):
      usr_input = input("Input: ")
      if usr_input == len(dupe) + 1:
         for f in dupe:
            listDir(os.path.dirname(f))

   
   return int(usr_input)



      
log("Dubly started working.", 1)


#1 = grün
#2 = gelb
#3 = rot
#4 = violet
#5 = blau

if not len(sys.argv) == 2:
    log("Error parsing Variable. First Argument should be a path, in which I will annihilate all dublicates.", 3)
    exit()
    
root_directory = str(sys.argv[1])


#check variables:
if not os.path.isdir(root_directory):
    log("Error parsing Variable. First Argument should be a valid path.", 3)
    exit()
    
root_directory = os.path.abspath(root_directory)

if not os.path.isdir(root_directory):
    log("Error parsing Variable. Absolut Path should be valid too. Caluclated absulut path: " + root_directory, 3)
    exit()
   
log("root_directory found file://" + root_directory, 0)



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
