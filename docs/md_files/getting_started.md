Getting Started
===================================

Terminology
------------------------------

The four most important terms in **FISSION** are: **Network**, **Client**, **Server** and **Job**.
Within a **Network** there is **one Client**, some number of **Server**s and a number of **Job**s.

### A Client ###

- **distributes** Jobs and their associated Files.
- **monitors** all Servers.
- **restarts** the Jobs of a Server within the Network in case of its failure. 

### A Server ###

- **executes** provided Jobs
- **receives** input data from other Servers
- **sends** output data to other Servers

### A Job ###

- **defines** a program and the Jobs it communicates with


Installation
------------

**Your Python version has to be 3.6 or greater!**

### Client ###

The Client is where you should copy the repository to and is the "supervisor" of your cluster, monitoring all servers and managing the failover.

**FISSION** depends on named pipes and therefore can not run on Windows.

**FISSION** is installable via pip. We recommend setting up a virtual environment and activating it:

```bash
python3 -m venv <my-virtual-environment>
source <my-virtual-environment>/bin/activate
```

Next install fission via pip:

```bash
pip3 install <fission-root-directory>
```

When developing we recommend to make an editable install by adding the `-e` flag.  

That's it, the Client is ready to run!

### Server ###

If you haven't already, install ansible. It is used to set up your servers automated, you only have to tweak a few setting.

> **On Windows**:
> There is no Windows version of ansible, but on Windows 10, you can simply install WSL (e.g., [Ubuntu](https://www.microsoft.com/de-de/p/ubuntu-1804-lts/9n9tngvndl3q)),
> which gives you a Linux subsystem running on top of your Windows machine.
> Then, you can open the Linux terminal and follow the instructions below, as if you were on Linux.

> **On Ubuntu**:
> [ansible documentation](http://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-releases-via-apt-ubuntu)  
> Commands:
>
>```bash
> sudo apt-get update
> sudo apt-get install software-properties-common
> sudo apt-add-repository ppa:ansible/ansible
> sudo apt-get update
> sudo apt-get install ansible make
> ```

> **On macOS**
>
> ```bash
> brew install ansible
> ```

You have to set all ips of your servers in the ```ansible/inventories/production/hosts.yml``` file. 
If the ip you are connecting to for installation differs from the one you wish you dispynode to serve just add a `dispy_ip` to the host.
You will find two examples, follow them.  
Now head to ```ansible/inventories/production/group_vars/fissionservers/setting.yml``` and change ```ansible_user``` to what ever user you set up on your servers. At this point you can also specify any additional python3 packages you wish to install for your jobs.

Run ```make servers_pw```. This will run the ansible playbook and ask for an ssh password and a sudo password.  
If you already copied an id to the server by running ```ssh-copy-id <server-address>``` (you maybe have to run ```ssh-keygen``` first to create a key), you can run ```make servers``` and it will only ask for a sudo password.

The following commands are also supported by the make file:

- `make start` starts the service running a dispynode on each node (`make servers starts the service automatically)

- `make stop` stops the service running a dispynode on each node

- `make renew` copies a new version of the fission.service file to the nodes and restarts the fission service.
  This is useful if you want to change the ip the dispynode serves or changed something in the `ansible/roles/setup/templates/fission.service.j2` file.
  E.g. you could ad `-d` flag to run the nodes in debug mode if you are experiencing issues.

**Make sure you run the same dispy versions on the client and all nodes, otherwise they will not detect each other.**

Your Network is ready now.


### Install and setup B.A.T.M.A.N-adv

Prior to installing BATMAN, make sure the device is connected to your ad-hoc network.

First you need to enable necessary interfaces on boot. 

`cd ~ && touch start-batman-adv.sh && chmod +x start-batman-adv.sh`

After creating the file, type in:

```
# Tell batman-adv which interface to use
sudo batctl if add wlan0
# Activates the interfaces for batman-adv
sudo ifconfig wlan0 up
sudo ifconfig bat0 up # bat0 is created via the first command
```

Note: *wlan0* in this case is the interface used for your ad-hoc network.

Next you need to configure the *bat0* interfaces, by creating a file in `/etc/network/interfaces.d` named bat0 with:

```
auto bat0
iface bat0 inet auto
    pre-up /usr/sbin/batctl if add wlan0
```
Finally, to install BATMAN-adv use:

```
# Install batman-adv
sudo apt-get install -y batctl
# Have batman-adv startup automatically on boot
echo 'batman-adv' | sudo tee --append /etc/modules
# Enable interfaces on boot
echo "$(pwd)/start-batman-adv.sh" >> ~/.bashrc
```

To complete the installation reboot your device.
To check if your installation succeeded, type
`sudo batctl -v`
and check if a batman-adv module is loaded
and type
`sudo batctl if`
to check whether wlan0 is active.




