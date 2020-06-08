#!/usr/bin/python3
# -*- coding: utf-8 -*-

#---------------------------
#
#   Name:dstart.py (VCML2 Cluster Start Utility) 
#   Python Script
#   Author: Scott P Morton (spm3c at mtmail.mtsu.edu)
# 
#   VCML is a cluster manager for Docker
#   Designed to configure and run a uniform docker cluster
#   for the purposes of education and demonstration
#
#---------------------------
#==============================================================================
#     dstart.py - Cluster start utility
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
Description = "VCML2 cluster modeling start utility"

import sys, platform, json, socket
import subprocess as subp
import vcml2_ver as ver

sys_OS = platform.system()
host = socket.gethostname()
debug = False

# takes command, message to display and action
# If action is less than 1 exit with error level
# If action is 1, return output
# else no action taken
def ProcessCMD(cmd, errorMsg, message, action):
    if debug:
        debugLogS.write(cmd + '\n\n')
            
    rc,output = subp.getstatusoutput(cmd)
    if rc:
        print(errorMsg,output)
        if debug:
            debugLogS.write(errorMsg + "\n" + output + '\n\n')
        if action < 1:
            sys.exit(action)
    else:
        if len(message) > 0:
            print(message)
        if debug:
            debugLogS.write(message + "\n" + output + '\n\n')
        if action == 1:
            return output
 
def _ReadConfig():
    global _cfg
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
   
def _Start(dbg):
    global debug
    debug = dbg

    if debug:
        try:
            global debugLogS
            debugLogS = open ('dstart.log', 'w')
        except OSError as err:
            print("\nFile creation error for dbuild.log\n\n")    
            print("OS error: {0}".format(err))
            sys.exit(-2)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            sys.exit(-2)

    global routers
    networks = _cfg["NETWORKS"]
    nodes = _cfg["NODES"]
    rte_table = _cfg["ROUTES"]

    print ("Starting ",ver.__title__,)
    if not(_cfg):
        print("System not configured, exiting...")
        sys.exit(-4)
    
    for key in nodes:
            
        command = "docker start " + key
        ProcessCMD(command,"Error encountered : node -" + key, \
                    "Node : " + key + " START completed", -3)

        command = "docker exec " + key + " /bin/bash -c '/etc/init.d/ssh start'"
        
        ProcessCMD(command,"Error encountered : node -" + key, \
                    "Node : " + key + " sshd started", -3)

    print(ver.__title__,"has started the environment\n")
    
    # setup routing 3/2/2016
    if (len(rte_table) > 0):
        print("Configuring routes")
        for key in nodes:
            if not(nodes[key]["router"]):
                links = nodes[key]["networks"]
                connected_routers = []
                for link in links:
                    for rtr in rte_table.keys():
                        if nodes[rtr]["networks"].__contains__(link):
                            connected_routers.append([rtr,link])
                if len(connected_routers) > 1:
                    for rtr,link in connected_routers:
                        for otherRtrs in rte_table[rtr]["table"].keys():
                            for nets in rte_table[rtr]["table"][otherRtrs]:
                                if link == nets:
                                    continue
                                command = "docker exec --privileged " + key + \
                                            " /bin/bash -c 'route add -net " + \
                                            networks[nets]["subnet"] + \
                                            " gw " + nodes[otherRtrs]["connections"][link] + \
                                            "'"
                                ProcessCMD(command,"Route already exists : node - " + key, \
                                            "Node : " + key + " route added", 2)

                elif len(connected_routers) == 1:
                    command = "docker inspect " + key
                    rc,output = subp.getstatusoutput(command)
                    cfg = json.loads(output)[0]
                    currentDefGW = cfg["NetworkSettings"]["Networks"][nodes[key]["networks"][0]]["Gateway"]
                    command = "docker exec --privileged " + key + \
                                " /bin/bash -c 'route del default gw " + \
                                currentDefGW + "'"
                    ProcessCMD(command,"Failed to delete def GW : node - " + key, \
                                "Node : " + key + " def GW removed", 2)
                    
                    command = "docker exec --privileged " + key + \
                                " /bin/bash -c 'route add default gw " + \
                                nodes[connected_routers[0][0]]["connections"][connected_routers[0][1]] + \
                                "'"
                    ProcessCMD(command, "error adding def GW : node - " + key, \
                                "Node : " + key + " def GW added", 2)
        
            else:
                for rtr in rte_table[key]["table"].keys():
                    for nets in rte_table[key]["table"][rtr]:
                        if nodes[key]["networks"].__contains__(nets):
                            router_connection = nets
                    for nets in rte_table[key]["table"][rtr]:
                        if nodes[key]["networks"].__contains__(nets):
                            continue
                        else:
                            command = "docker exec --privileged " + key + \
                                " /bin/bash -c 'route add -net " + \
                                networks[nets]["subnet"] + " gw " + \
                                nodes[rtr]["connections"][router_connection] + \
                                "'"
                            ProcessCMD(command,"error adding route : node - " + key, \
                                       "Node : " + key + " route added", 2)
    if debug:
        debugLogS.close()
        
if __name__ == "__main__":

    if(len(sys.argv) > 1):
        if(sys.argv[1].upper() == "--HELP" or sys.argv[1].upper() == "-H"):
            print("This tool builds the cluster model from the config file\n")
            sys.exit(0)
        elif sys.argv[1].upper() == "--DEBUG" or sys.argv[1].upper() == "-D":
            debug = True
            
        else:
            print("Invalid argument given, options are --help, -h, --debug, -d or None\n")    
            sys.exit(1)
    
        print ("\n\nThis is the",Description,\
                "\nVCML2 version:",ver.__version__,\
                "\nWritten by:",ver.__author__, "\n\n")
    _ReadConfig()
    _Start(debug)
    print("\nCluster model is ready for use\n")

