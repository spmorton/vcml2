#!/usr/bin/python3
# -*- coding: utf-8 -*-

#---------------------------
#
#   Name:dremove.py (VCML2 Configuration Remover) 
#   Python Script
#   Author: Scott P Morton (spm3c at mtmail.mtsu.edu)
# 
#   VCML is a cluster manager for Docker
#   Designed to configure and run a uniform docker cluster
#   for the purposes of education and demonstration
#
#---------------------------
#==============================================================================
#     dremove.py - Cluster configuration removal tool
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
Description = "VCML2 cluster modeling removal tool"

import sys, platform, json, socket
import subprocess as subp
import dstop as stop
import vcml2_ver as ver

global host

sys_OS = platform.system()
host = socket.gethostname()

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

decision = input("\n\nRemove " + ver.__title__ + " from this machine? yes/NO: ") or "No"
if (not(decision.upper() == "YES")):
    sys.exit(0)

nets = _cfg["NETWORKS"]
nodes = _cfg["NODES"]    

def _Remove():
    print("Removing",ver.__title__,"\n")
    stop._Stop()

    print("\nContinuing with removal process\n")
    
    for key in nodes:
        command = "docker rm " + key
        rc,output = subp.getstatusoutput(command)
        if rc:
            print("Error encoutered :",output)

        print("Container :", key, "REMOVE completed")

    print("\nRemoving custom networks")
    for key in nets:
        command = "docker network rm " + key
        rc,output = subp.getstatusoutput(command)
        if rc:
            print(output)
        else:
            print("Network :", key, "removed")
    
    print()
    print(ver.__title__,"containers and custom networks have been removed\n")

if __name__ == "__main__":
    print ("\n\nThis is the",Description,\
            "\nVCML2 version:",ver.__version__,\
            "\nWritten by:",ver.__author__, "\n\n")
    
    if(len(sys.argv) > 1):
    
        if(sys.argv[1].upper() == "--HELP" or sys.argv[1].upper() == "-H"):
            print("This utility removes the cluster and network configuration from this system\n")
            sys.exit(0)
        else:
            print("Invalid argument given, options are --help or -h or None\n")    
            sys.exit(-1)

    _Remove()
    
