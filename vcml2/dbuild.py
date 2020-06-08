#!/usr/bin/python3
# -*- coding: utf-8 -*-

#---------------------------
#
#   Name:dbuild.py (VCML2 Configuration Builder) 
#   Python Script
#   Author: Scott P Morton (spm3c at mtmail.mtsu.edu)
# 
#   VCML is a cluster manager for Docker
#   Designed to configure and run a uniform docker cluster
#   for the purposes of education and demonstration
#
#---------------------------

#==============================================================================
#     dbuild.py - Cluster build tool
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
Description = "VCML2 cluster modeling build tool"

import sys, platform, json, socket, ipaddress
import subprocess as subp

import dstart as start
import vcml2_ver as ver

sys_OS = platform.system()

debug = False
host = socket.gethostname()
syntaxFlag = False
errorFlag = False

print ("\n\nThis is the",Description,\
        "\nVCML2 version:",ver.__version__,\
        "\nWritten by:",ver.__author__, "\n\n")

if(len(sys.argv) > 1):
    if(sys.argv[1].upper() == "--HELP" or sys.argv[1].upper() == "-H"):
        print("This tool builds the cluster model from the config file\n")
        sys.exit(0)
    elif sys.argv[1].upper() == "--DEBUG" or sys.argv[1].upper() == "-D":
        debug = True
        try:
            global debugLog
            debugLog = open ('dbuild.log', 'w')
        except OSError as err:
            print("\nFile creation error for dbuild.log\n\n")    
            print("OS error: {0}".format(err))
            sys.exit(-2)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            sys.exit(-2)
        
    else:
        print("Invalid argument given, options are --help, -h, --debug, -d or None\n")    
        sys.exit(-1)

try:
    with open ( 'config.json', 'r' ) as cfg:
        _cfg  =  json.load(cfg)

except OSError as err:
    print("config.json file not found.\n")
    print("VCML2 uses relative paths, are you sure you are in the right directory?")
    print("OS error: {0}".format(err))
    sys.exit(-2)
except ValueError as err:
    print("Unexpected error or json syntax error detected.\n", sys.exc_info()[0])
    print (err,"in config.json")
    sys.exit(-2)
    
lexica = {
        "net": {
            "driver": "--driver=",
            "subnet": "--subnet=",
            },
        "node": {
            "hostname": "--hostname=",
            "image": "image",
            "router": "",
            "networks": "",
            "volume": "--volume="
            }
        }

_cfg["ROUTES"] = {}
subnets = {}
address = {}
hosts = {}
uniqueHosts = {} 

rte_table = _cfg["ROUTES"]
networks = _cfg["NETWORKS"]
nodes = _cfg["NODES"]
net = lexica["net"]
node = lexica["node"]

# takes command, message to display and action
# If action is less than 1 exit with error level
# If action is 1, return output
# else no action taken
def ProcessCMD(cmd, message, action):
    if debug:
        debugLog.write(cmd + '\n\n')
            
    rc,output = subp.getstatusoutput(cmd)
    if rc:
        print(output)
        if debug:
            debugLog.write(output + '\n\n')
        if action < 1:
            sys.exit(action)

    else:
        if len(message) > 0:
            print(message)
        if debug:
            debugLog.write(message + "\n" +output + '\n\n')
        if action == 1:
            return output
    
# Validate setup
command = "docker --version"
output = ProcessCMD(command, " ", 1)
(major,minor,rev) = output.split(sep=" ")[2].split(sep=",")[0].split(sep=".")
if (int(major) < 1 or int(minor) < 10):
    print("VCML requires docker version 1.10 or greater to run")
    sys.exit(-6)

# Check config.json for proper syntax
for key in networks:
    for attribute in networks[key]:
        if (not(net.get(attribute))) :
            syntaxFlag = True
            print("syntax error at NETWORKS ", key, attribute, "\n")

for key in nodes:
    links = nodes[key]["networks"]
    if (nodes[key]["router"]):
        if (len(links) < 2):
            syntaxFlag = True
            print("syntax error at NODES ", key, links, "\n" \
                "defined as router but only assigned to one network\n")
                
    for attribute in nodes[key]:
        if (attribute == "networks" or attribute == "router"):
            continue
        elif not(node.get(attribute)):
            syntaxFlag = True
            print("syntax error at NODES ", key, attribute, "\n")

if syntaxFlag:
    print("Syntax error\n\nPlease refer to the errors listed above\n\n")
    sys.exit(-5)
else:
    print("Syntax checking completed successfully...\n\n")
    decision = input("continue... Y/n : ") or "Y"
    if not(decision.upper() == "Y"):
        sys.exit(0)

# Build out the subnets for address management
for key in networks:
    subnets[key] = ipaddress.ip_network(networks[key]["subnet"])
    address[key] = []
    for addr in subnets[key]:
        address[key].append(addr)
    # Pop reserved and Docker used address
    address[key].pop()
    address[key].reverse()
    address[key].pop()
    address[key].pop()
    
# assign all addresses
for key in nodes:
    links = nodes[key]["networks"]
    nodes[key]["connections"] = {}
    if networks:
        for link in links:
            net_link = link
            hostkey = nodes[key]["hostname"] + "." + link
            if nodes[key]["router"]:
                hosts[hostkey] = address[link][0].exploded
                address[link].remove(address[link][0])
            else:
                hosts[hostkey] = address[link].pop().exploded
            nodes[key]["connections"][link] = hosts[hostkey]

print("\n\nBuilding ",ver.__title__," cluster model\n")

print("\nCreating Networks\n")
for key in networks:
    last = ""
    command = "docker network create "
    for attribute in networks[key]:
        command = command + net[attribute] + networks[key][attribute] + " "
    command = command + key
    ProcessCMD(command,"Network configured as : " + key, 2)

print("\nNetwork setup complete\n\n")
print("Configuring Nodes\n\n")

# create nodes    
for key in nodes:

    links = nodes[key]["networks"]

    command = "docker run -d -it "
    for attribute in nodes[key]:
        if (attribute == "networks" or attribute == "router" or attribute == "connections"):
            continue
        if (attribute == "image"):
            image = nodes[key][attribute]
            continue
        command = command + node[attribute] + nodes[key][attribute] + " "

    for link in links:
        net_link = link
        command = command + "--net=" + link + " "
        if networks:
            command = command + "--ip=" + nodes[key]["connections"][link] + " "
        break
    for obj in hosts:
        command = command + "--add-host=" + obj + ":" + hosts[obj] + " "

    # Important - must have image name as the last build parameter followed by 
    # the command to 'run'
    command = command + "--name=" + key + " "       
    command = command + image + " /bin/bash"
    ProcessCMD(command,"Node "+ key + " configured as : " + key,2)    

    for link in links:
        command = "docker network connect "
        if (link == net_link):
            continue
        else:
            links = nodes[key]["connections"]
            if links.get(link):
                command = command + "--ip=" + nodes[key]["connections"][link] + " "
            command = command + link + " "
            command = command + key + " "
            ProcessCMD(command,"Node " + key + " added network : " + link,2)

    if nodes[key]["router"]:
        command = "docker exec --privileged " + key + \
                    " /bin/bash -c 'sed -i /#net.ipv4.ip_forward/s/#//g /etc/sysctl.conf'"
        ProcessCMD(command,"Node " + key + " configured as a router",2)

    # these two commands correct a bug potential in images built from a tar file
    command = "docker exec --privileged " + key + \
                " /bin/bash -c 'chmod u+s  /bin/ping'"
    ProcessCMD(command,"",2)

    command = "docker exec --privileged " + key + \
                " /bin/bash -c 'chmod 4755 /bin/su'"
    ProcessCMD(command," ",2)

print("\nNodes created, continuing configuration of environment\n")

# routing 3/2/2016
routers = {}
for key in nodes:
    if nodes[key]["router"]:
        routers[key] = nodes[key]["networks"]
            
if (len(routers) > 0):
    #Build relational matrix of network nodes
    for router in routers:
        rte_table[router]={"knwn_nts":[],"knwn_rtrs":[],"table":{}}
        current_rtr = rte_table[router]
        rtrs = routers.copy()
        useless = rtrs.pop(router)
        frtrs =[]
        for net in nodes[router]["networks"]:
            for rtr in rtrs:
                if nodes[rtr]["networks"].__contains__(net):
                    associated_nets = nodes[rtr]["networks"].copy()
                    associated_nets.remove(net)
                    current_rtr["knwn_nts"].append({rtr:associated_nets})
                    current_rtr["knwn_rtrs"].append(rtr)

    # Build graph of the network in relation to routers
    global net_graph
    net_graph = {}
    for router in rte_table.keys():
        if net_graph.__contains__(router):
            for rtr in rte_table[router]["knwn_rtrs"]:
                net_graph[router].append(rtr)
        else:
            net_graph[router] = []
            for rtr in rte_table[router]["knwn_rtrs"]:
                net_graph[router].append(rtr)

    # Build routing tables for each router
    # Function 'find_route()' derived from the python documentation library @
    # https://www.python.org/doc/essays/graphs/
    def find_route(start, end, route=[]):
        route = route + [start]
        if start == end:
            return route
        
        if not net_graph.__contains__(start):
            return None
        
        least_cost = None
        for net in net_graph[start]:
            if net not in route:
                newroute = find_route(net, end, route)
                if newroute:
                    if not least_cost or len(newroute) < len(least_cost):
                        least_cost = newroute
        return least_cost

    for router in routers:
        current_rtrs = routers.copy()
        useless = current_rtrs.pop(router)
        for other_rtr in current_rtrs:
            trgt_route = find_route(router,other_rtr)
            trgt_route.remove(router)
            neighbor_rtr = trgt_route[0]
            if not rte_table[router]["table"].__contains__(neighbor_rtr):
                rte_table[router]["table"][neighbor_rtr] = []
            for trgt_rtr in trgt_route:
                for net in nodes[trgt_rtr]["networks"]:
                    if  rte_table[router]["table"][neighbor_rtr].__contains__(net):
                        continue
                    rte_table[router]["table"][neighbor_rtr].append(net)
            
try:
    hostsd_File = open ('hostsd', 'w')
    shostequiv_File = open ('shosts.equiv', 'w')
    hostnames_File = open ('hostnames', 'w')
    configVCML_File = open ('config.vcml', 'w')

    configVCML_File.truncate()
    hostsd_File.truncate()
    hostnames_File.truncate()
    shostequiv_File.truncate()

except OSError as err:
    print("\nFile creation error for hostd, hostnames, shosts.equiv, config.vcml\n\n")    
    print("OS error: {0}".format(err))
    sys.exit(-2)
except:
    print("Unexpected error:", sys.exc_info()[0])
    sys.exit(-2)

# Build list of unique hosts, write out compiled information
for key in hosts:
    uniqueHosts[key.split(sep=".")[0]] = key

for key in uniqueHosts:
    hostsd_File.write(uniqueHosts[key] + '\n')
    shostequiv_File.write(uniqueHosts[key] + '\n')
    shostequiv_File.write(hosts[uniqueHosts[key]] + '\n')

hostnames_File.write(json.dumps(hosts, sort_keys=True, indent=4))
configVCML_File.write(json.dumps(_cfg, sort_keys=True, indent=4))

shostequiv_File.close()
hostsd_File.close()
hostnames_File.close()
configVCML_File.close()

# If nodes were created, start them and sync up the ssh keys
if nodes:

    start._ReadConfig()
    start._Start(debug)

    print()
    print(ver.__title__,"is synching up ssh keys where possible for host based authentication\n", \
            "This may take a moment!\n\n")

    # Sync up keys and ring of trust
    for key in nodes:
        for hostnames in hosts:
            command = "docker exec " + key + " /bin/bash -c 'ssh-keyscan \
                        -t rsa,dsa " + hostnames + " >> /etc/ssh/ssh_known_hosts'"
            ProcessCMD(command,"",2)
    
        command = "docker cp shosts.equiv " + key + ":/etc/ssh/shosts.equiv"
        ProcessCMD(command,"",2)

if debug:
    debugLog.close()

print()
print(ver.__title__,"has completed building the cluster model\n\n")

