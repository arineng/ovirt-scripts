#!/usr/bin/env python
#
# Based on a script by Pablo Iranzo Gomez (Pablo.Iranzo@redhat.com)
#
# Description: Script for creating VM's
#
#
# This software is based on GPL code so:
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.

import sys
import getopt
import optparse
import os
import time
import json
import getpass

from ovirtsdk.api import API
from ovirtsdk.xml import params

description = """
vmcreate is a script for creating vm's based on specified values

vmcpu    defines the number of CPUs
sdtype can be: SD to use
sdsize can be: Storage to assing
vmgest can be: ovirtmgmt, or your defined networks
osver can be: rhel_6x64, etc
"""

# Option parsing
p = optparse.OptionParser("rhev-vm-create.py [arguments]", description=description)
p.add_option("-u", "--user", dest="username", help="Username to connect to ovirt-engine API", metavar="admin@internal", default="admin@internal")
p.add_option("-w", "--password", dest="password", help="Password to use with username", metavar="admin", default="redhat")
p.add_option("-s", "--server", dest="server", help="RHEV-M server address/hostname to contact", metavar="server", default="127.0.0.1")
p.add_option('-v', "--verbosity", dest="verbosity", help="Show messages while running", metavar='[0-n]', default=0, type='int')
p.add_option("-n", "--name", dest="name", help="VM name", metavar="name", default="name")
p.add_option("-c", "--cluster", dest="cluster", help="VM cluster", metavar="cluster", default="Default")
p.add_option("--vmcpu", dest="vmcpu", help="VM CPU", metavar="vmcpu", default="1")
p.add_option("--vmmem", dest="vmmem", help="VM RAM in GB", metavar="vmmem", default="1")
p.add_option("--sdtype", dest="sdtype", help="SD type", metavar="sdtype", default="Default")
p.add_option("--sdsize", dest="sdsize", help="SD size in GB", metavar="sdsize", default="20")
p.add_option("--osver", dest="osver", help="OS version", metavar="osver", default="rhel_6x64")
p.add_option("--vmnet", dest="vmnet", help="Network to use", metavar="vmnet", default="rhevm")
p.add_option("--config", dest="config", help="JSON config file")
p.add_option("--storage", dest="storage_name", help="Name of the storage domain")
p.add_option("--ca", dest="ca_file", help="Path to the ca file")
p.add_option("--insecure", dest="insecure", help="Connect without validating the CA")
(options, args) = p.parse_args()

# Use the json file to update configs if present
if options.config:
    with open(options.config) as config_params:
        locals().update(json.load(config_params))

# Overide anything in the config file
# on the command line
if options.username:
    username = options.username
if options.server:
    server = options.server
if options.name:
    name = options.name
if options.cluster:
    cluster = options.cluster
if options.vmcpu:
    vmcpu = options.vmcpu
if options.vmem:
    vmem = options.vmem
if options.sdtype:
    sdtype = options.sdtype
if options.sdsize:
    sdsize = options.sdsize
if options.osver:
    osver = options.osver
if options.vmnet:
    vmnet = options.vmnet
if options.verbosity:
    verbosity = options.verbosity
if options.storage_name:
    storage_name = options.storage_name
if options.ca_file:
    ca_file = options.ca_file
if options.insecure:
    insecure = options.insecure

# Allow for interactive password auth
if options.password:
    password = options.password
else:
    password = getpass.getpass()


baseurl = "https://%s" % (server)

if options.insecure:
    api = API(url=baseurl, username=username, password=password, insecure=True)
else:
    api = API(url=baseurl, username=username, password=password, ca_file=ca_file)

try:
    value = api.hosts.list()
except:
    print "Error accessing RHEV-M api, please check data and connection and retry"
    sys.exit(1)


# Define the function to add vms
def add_vm(vmparams, name, vmdisk, nic_net1):
    try:
        api.vms.add(vmparams)
    except:
        print "Error creating VM with specified parameters, recheck"
        sys.exit(1)

    if verbosity > 1:
        print "VM created successfuly"

    if verbosity > 1:
        print "Attaching networks and boot order..."
    vm = api.vms.get(name=name)
    vm.nics.add(nic_net1)

    try:
        vm.update()
    except:
        print "Error attaching networks, please recheck and remove configurations left behind"
        sys.exit(1)

    if verbosity > 1:
        print "Adding HDD"
    try:
        vm.disks.add(vmdisk)
    except:
        print "Error attaching disk, please recheck and remove any leftover configuration"
        sys.ext(1)

    if verbosity > 1:
        print "VM creation successful"

    vm = api.vms.get(name=name)
    vm.high_availability.enabled = True
    vm.update()

    #wait until VM is stopped before we start it.
    status = api.vms.get(name=name).status.state
    while status != 'down':
        print status
	time.sleep(1)
	status = api.vms.get(name=name).status.state
	vm.start()

# Define VM based on parameters
if __name__ == "__main__":
    vmparams = params.VM(os=params.OperatingSystem(type_=osver),
            cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcpu))),
            name=name, 
            memory=1024 * 1024 * 1024 * int(vmmem),
            cluster=api.clusters.get(name=cluster),
            template=api.templates.get(name="Blank"), type_="server")
    
    vmdisk = params.Disk(
            size=1024 * 1024 * 1024 * int(sdsize), 
            wipe_after_delete=True, 
            sparse=True, 
            interface="virtio", 
            type_="System", 
            format="cow",
            storage_domains=params.StorageDomains(storage_domain=[api.storagedomains.get(name=storage_name)]))
    
    vmnet = params.NIC()
    network_net = params.Network(name=vmnet)
    nic_net1 = params.NIC(name='nic1', network=network_net, interface='virtio')

    add_vm(vmparams, name, vmdisk, nic_net1)
#print "MAC:%s" % vm.nics.get(name="eth0").mac.get_address()
