# oVirt scripts

These scripts require the package ovirt-engine-sdk-python from pypi at https://pypi.python.org/pypi/ovirt-engine-sdk-python

Use this script to create a VM remotely on ovirt/RHEV

Options can either be set via command line or via a .json file that you can declare with --config

The following options are necessary:

1. username - the username you log into the manager with, if set without -w the password will be prompted for
2. server - the ovirt/RHEV manager to do the provisioning
3. name - give your server a name
4. cluster - make sure to identify the cluster under which you'll install the vm
5. sdsize - the size of the storage disk
6. vmnet - the network to attach to the primary interface

Sample json data
```json
{
	"name": "test-example-dev",
	"cluster": "CLUSTER",
	"vmcpu": "1",
	"vmmem": "4",
	"sdsize": "100",
	"vmnet": "NET",
	"storage": "STORAGE-FAST"
}
```
