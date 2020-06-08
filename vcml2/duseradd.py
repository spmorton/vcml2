# -*- coding: utf-8 -*-

#---------------------------
#
#   Name:duseradd.py (VCML2 Configuration Generator) 
#   Python Script
#   Author: Scott P Morton (spm3c at mtmail.mtsu.edu)
# 
#   VCML is a cluster manager for Docker
#   Designed to configure and run a uniform docker cluster
#   for the purposes of education and demonstration
#
#---------------------------

#==============================================================================
#     dconfig.py - Cluster user tool
#     Copyright (C) 2016  Scott P Morton
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
#==============================================================================

__title__  = "VCML2"
__author__ = "Scott P Morton (spm3c at mtmail.mtsu.edu)"
Description = "VCML2 cluster modeling user tool"

import sys, json, os, getpass
import subprocess as subp
import vcml2_ver as ver

print ("\n\nThis is the",Description,\
        "\nVCML2 version:",ver.__version__,\
        "\nWritten by:",ver.__author__, "\n\n")

if(len(sys.argv) > 1):
    if(sys.argv[1].upper() == "--HELP" or sys.argv[1].upper() == "-H"):
        print("This tool generates the configuration file for the cluster\n", \
                "Follow the prompts carefully and read the installation guide\n", \
                "prior to continuing. Otherwise, taking the defaults will result\n", \
                "in a single host cluster with three containers running with the\n", \
                "current users home folder mounted in each nodes home folder.\n")
        sys.exit(0)
    else:
        print("Invalid argument given, options are --help or -h or None\n")    
        sys.exit(-1)

try:
    with open ( 'config.vcml', 'r' ) as cfg:
            _cfg  =  json.load(cfg)
except OSError as err:
    print("config.vcml file not found or json syntax error detected.\n")
    print("VCML2 uses relative paths, are you sure you are in the right directory?")
    print("OS error: {0}".format(err))
    sys.exit(-2)
except ValueError as err:
    print("Unexpected error or json syntax error detected.\n", sys.exc_info()[0])
    print (err,"in config.vcml")
    sys.exit(-2)

nodes = _cfg["NODES"]
_usr = {}

ENV = os.environ
decision = input("\nUse current user name for containers '"+ENV["LOGNAME"]+ \
                 "' [Yes]/no: ") or "Yes"
if(not(decision.upper() == "YES" )):
    _usr["LOGNAME"] = input("Enter the user id to use: ")
else:
    _usr["LOGNAME"] = ENV["LOGNAME"]

print("\n\nA password is required to create the user account in the containers.\n",
      "A minimum of 5 characters is required. It is recommended to not\n",
      "use your current user password for the containers and strongly\n",
      "suggested some complexity be used as is required on some systems\n")
      
while(True):
    pw = getpass.getpass(prompt="Enter the password: ")
    if(len(pw) < 5):
        print("A password of at least 5 characters is required, please try again\n")
        continue
    else:
        pw2 = getpass.getpass(prompt="Re-Enter the password: ")
        if (pw == pw2):
            break
        else:
            print("Passwords entered do not match, please try again\n\n")
            continue

_usr["PW"] = pw

decision = input("Enter a preffered shell i.e.([bash],csh,tcsh,ksh)? y/N : ") or "N"
shells = ["/bin/bash","/bin/csh","/bin/ksh","/bin/tcsh"]
if (decision.upper() == "Y"):
    for i in range(len(shells)):
        print(i,"-",shells[i])
    while (True):
        decision = input("Enter your selection (0,1,2,...) : ")
        if (decision.isdigit() and int(decision) >= 0 and int(decision) < len(shells)):
            _usr["SH"] = shells[int(decision)]
            break
        else:
            print("\n\nInvalid selection, please try again\n\n\n")

else:
    _usr["SH"] = shells[0]

print("\n\nBecause this software runs on multiple platforms, you are required to gather\n", \
        "your linux id number manually and input it here. This can be accomplished\n", \
        "by running the command 'id' from a linux term session and inputing the\n", \
        "number after 'uid' into this prompt, i.e.\n", \
        "uid=1000(scott) gid=100(users) groups=100(users),490(docker)\n", \
        "would use 1000 as the entry\n\n")

while True:
    entry = input("Enter your 'uid' number : ")
    if not(entry.isdigit()):
        print("\n\nInvalid entry, entry must be a number!\n\n")
    else:
        _usr["UID"] = entry
        break

for key in nodes:
    command = "docker exec " + key + " /bin/bash -c \"useradd -m " + \
                "-u " +  _usr["UID"] + \
                " -s " + _usr["SH"] + \
                " -p \'" + _usr["PW"] + \
                "\' " + _usr["LOGNAME"] + "\""
    rc,output = subp.getstatusoutput(command)
    if rc:
        print(output)
    else:
        print(output)
    info = _usr["LOGNAME"] + ":" + _usr["PW"]
    command = "docker exec " + key + " /bin/bash -c 'echo '" + info + "' | chpasswd'"
    rc,output = subp.getstatusoutput(command)
    if rc:
        print(output)
    else:
        print(output)
