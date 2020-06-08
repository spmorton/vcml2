#!/usr/bin/python3
# -*- coding: utf-8 -*-

#---------------------------
#
#   Name:dstop.py (VCML2 Cluster Stop Utility) 
#   Python Script
#   Author: Scott P Morton (spm3c at mtmail.mtsu.edu)
# 
#   VCML is a cluster manager for Docker
#   Designed to configure and run a uniform docker cluster
#   for the purposes of education and demonstration
#
#---------------------------
#==============================================================================
#     dstop.py - Cluster stop utility
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
Description = "VCML2 cluster modeling stop utility"

import sys, platform, json, socket
import subprocess as subp
import vcml2_ver as ver

sys_OS = platform.system()
host = socket.gethostname()

def _Stop():
    global _cfg
    
    try:
        with open ('config.vcml','r') as cfg:
            _cfg = json.load(cfg)
    except OSError as err:
        print("config.vcml file not found or json syntax error detected.\n")
        print("VCML2 uses relative paths, are you sure you are in the right directory?")
        print("OS error: {0}".format(err))
        sys.exit(-2)
    except ValueError as err:
        print("Unexpected error or json syntax error detected.\n", sys.exc_info()[0])
        print (err,"in config.vcml")
        sys.exit(-2)

    print ("Stopping ",ver.__title__,)

    nodes = _cfg["NODES"]

    for key in nodes:
        command = "docker stop " + key
        rc,output = subp.getstatusoutput(command)
        if rc:
            print("Error encounter : ",output)
        else:
            print("Node :", key, "STOP completed")

    print(ver.__title__,"Has stopped the environment\n")
    
if __name__ == "__main__":

    if(len(sys.argv) > 1):
        if(sys.argv[1].upper() == "--HELP" or sys.argv[1].upper() == "-H"):
            print("This utility stops the containers associated with the cluster config\n")
            sys.exit(0)
        else:
            print("Invalid argument given, options are --help or -h or None\n")    
            sys.exit(-1)
    
    
    print ("\n\nThis is the",Description,\
            "\nVCML2 version:",ver.__version__,\
            "\nWritten by:",ver.__author__, "\n\n")

    _Stop()
