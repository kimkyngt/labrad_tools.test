# Initial installation of Debian

1.  Download the Debian installation iso

2.  Install the ISO on a USB stick (from Ubuntu computer).  Be VERY careful that you use the correct path for the USB drive, as this command could overwrite an important hard drive if the wrong path is used.

```bash
>> sudo dd if=<path to iso> of=<path to usb drive> bs=1M
>> sync
```

3.  Install Debian on YeElmo using the USB.  Set up the username as srgang and use the usual user password.  When the computer restarted the desktop environment initially wouldn't load.  Ross did the following:

```bash
>> su
>> sudo apt-get install gnome-shell
>> systemctl disable gdm
>> reboot
```

4.  Initially, Debian needs a bit of configuring before we can make any progress.  The first thing we did was install sudo, configure the sudoers file using visudo, and add ourself to the sudo group.  We found that this didn't take effect until we rebooted the computer:

```bash
>> su
>> apt-get install sudo
>> visudo   #If commented, uncomment the line:  %sudo   ALL=(ALL:ALL) ALL
>> usermod -aG sudo srgang
>> reboot
```

5.  Now we can install some software.  Install python-dev, pip, and git:

```bash
>> sudo apt-get install python-dev
>> sudo apt-get install python-pip
>> sudo apt-get install git
```

6.  Mount the Z drive at /home/srgang/yedata.  First install:

```bash
>> sudo apt-get install cifs-utils
>> mkdir /home/srgang/yedata
```

And add the following line to /etc/fstab

```bash
//yedata.colorado.edu/Sr /home/srgang/yedata cifs credentials=/home/srgang/.yesrdata_credentials,uid=1000,gid=10 0 0
```

And create the credentials file /home/srgang/.yesrdata_credentials:

```bash
username=srgang
password=<usual with ! at end>
```

Finally mount the Z drive:

```bash
>> sudo mount -a
```

7.  Configure the second ethernet port to have a static IP address 192.168.1.8 on the Sesame Street network.  Add the following lines to /etc/network/interfaces:

```bash
allow-hotplug enp0s31f6
iface enp0s31f6 inet static
        address 192.168.1.8
        netmask 255.255.255.0
```

# Installing and configuring the labrad manager and labrad node

1. First, get the SrE git from github.  From the home directory

```bash
>> git clone https://github.com/PickyPointer/SrE
```

Our labrad_tools git repo now lives at /home/srgang/SrE/labrad_tools

2.  We want this computer to run the labrad-manager server, so we need to install scalabrad.  I decided to use the same version used on yesr10 (sr2 labrad manager).  I have stored a copy on the Z drive at SrE/software.

```bash
>> mkdir /home/srgang/scalabrad
>> cp yedata/SrE/software/scalabrad-web-server-2.0.5.tar.gz /home/srgang/scalabrad
>> cp yedata/SrE/software/scalabrad-0.8.3.tar.gz /home/srgang/scalabrad
>> cd ~/scalabrad
>> tar -zxvf scalabrad-0.8.3.tar.gz
>> tar -zxvf scalabrad-web-server-2.0.5.tar.gz
```

3.  Copy over the labrad systemd files to /etc/systemd/system/:

```bash
>> sudo cp -r labrad-node.service.d /etc/systemd/system
```

4.  Configure the service files.  /etc/systemd/system/labrad-manager.service:

```bash
[Unit]
Description=labrad manager
After=syslog.target

[Service]
Type=simple
User=srgang
Group=srgang
WorkingDirectory=/home/srgang/scalabrad/scalabrad-0.8.3/
ExecStart=/home/srgang/scalabrad/scalabrad-0.8.3/bin/labrad --tls-required=false --password=<usual with !>
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

/etc/systemd/system/labrad-web.service:
```bash
[Unit]
Description=labrad manager
After=syslog.target

[Service]
Type=simple
User=srgang
Group=srgang
WorkingDirectory=/home/srgang/scalabrad/scalabrad-web-server-2.0.5/
ExecStart=/home/srgang/scalabrad/scalabrad-web-server-2.0.5/bin/labrad-web --host 0.0.0.0
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

/etc/systemd/systemd/labrad-node.service:

```bash
[Unit]
Description=labrad node
After=network-online.target

[Service]
Type=simple
User=srgang
Group=srgang
WorkingDirectory=/home/srgang/SrE/labrad_tools
ExecStart=/usr/bin/python -m labrad.node
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```
/etc/systemd/system/labrad-node.service.d/labrad-node.conf:

```bash
Environment="LABRADHOST=192.168.1.8"
Environment="LABRADPASSWORD=<usual with !>"
Environment="LABRADNODE=yeelmo"
Environment="LABRAD_TLS=off"
Environment="PYTHONPATH=/home/srgang/SrE/labrad_tools/"
```

5.  Add the following to /home/srgang/.bash_profile
```bash
export LABRADHOST=host_name_goes_here
export LABRADNODE=node_name_goes_here
export LABRADPASSWORD=password_goes_here
export LABRAD_TLS=off
export PYTHONPATH="home/srgang/SrE/labrad_tools"
```

And to /home/srgang/.bashrc:
```bash
source /home/srgang/.bash_profile
```

Source .bashrc or open a new terminal.

6.  Enable and start the labrad services.  This will cause labrad to start now and automatically every time the computer is rebooted:

```bash
>> sudo systemctl enable labrad-manager
>> sudo systemctl enable labrad-web
>> sudo systemctl enable labrad-node
>> sudo systemctl start labrad-manager
>> sudo systemctl start labrad-web
>> sudo systemctl start labrad-node
```
Labrad should now be running.

# Setup for labrad_tools

1.  Install dependencies.  General:

```bash
>> sudo pip install pylabrad
>> sudo pip install ipython
>> sudo pip2 install service_identity 
>> sudo apt-get install matplotlib   #I had issues installing this through pip
>> sudo apt-get install python-qt4
>> sudo pip install inflection
>> pip install h5py
>> pip install scipy
```

For serial_server.  Note that the computer must be rebooted before srgang will have access to the dialout group (required for using serial_server):

```bash
>> sudo apt-get remove --purge brltty
>> sudo usermod -aG dialout srgang
>> sudo pip install pyserial==2.7
```

For picoscope server.  Note that the computer must be rebooted before srgang will have access to the pico group.

```bash
>> sudo bash -c 'echo "deb https://labs.picotech.com/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope.list'
>> wget -O - https://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add -
>> sudo apt-get update
>> sudo apt-get install picoscope
>> sudo apt-get install libps3000a
>> sudo pip2 install picoscope
>> sudo usermod -aG pico srgang
>> sudo cp /home/srgang/yedata/SrE/software/ps3000a.py /usr/local/lib/python2.7/dist-packages/picoscope
# the last line installs a modified version of the ps3000a library for pico-python
```

For okfpga server.  Again, I use an old version of the opal kelly library.

```bash
>> cp /home/srgang/yedata/SrE/software/FrontPanel-Ubuntu16.04LTS-x64-4.5.6.tgz /home/srgang/Downloads
>> cd /home/srgang/Downloads
>> tar -zxvf FrontPanel-Ubuntu16.04LTS-x64-4.5.6.tgz 
>> cd FrontPanel-Ubuntu16.04LTS-x64-4.5.6/
>> ./install.sh #Install frontpanel software
>> cp API/Python/ /usr/local/lib.python2.7/dist-packages/ok #Install python library "ok"
```
2.  Configure labrad node "yeelmo".  This will cause certain servers to run in the background when the computer boots up.  Open an ipython2 terminal and enter the following:

```python
#Establish labrad connection
import labrad
cxn = labrad.connect()

#Go to yeelmo Node
r = cxn.registry
r.cd('Nodes')
r.cd('yeelmo')

#Add labrad_tools to 'directories' so it can see the server code
r.set('directories', ['/home/srgang/SrE/labrad_tools/'])
cxn.node_yeelmo.refresh_servers()

#List available servers (to double-check that it worked)
cxn.node_yeelmo.available_servers()

#Add any servers that we want to run automatically:  
cxn.node_yeelmo.autostart_add('serial')
cxn.node_yeelmo.autostart_add('rf')
cxn.node_yeelmo.autostart_add('okfpga')
cxn.node_yeelmo.autostart_add('sequencer')
cxn.node_yeelmo.autostart_add('picoscope')
cxn.node_yeelmo.autostart_add('pmt')

#Call the autostart function if you want to run the server right now
cxn.node_yeelmo.autostart()
```

# Setting up a samba server for the J drive

1. Install and configure samba:

```bash
#Install samba on yeelmo
>> sudo apt-get install samba

#Create username 
>> sudo smbpasswd -a srgang
#enter new password
New SMB password:<usual with !>
```

2. Create folder for J drive mount point (for convenience):
```bash
>> mkdir /home/srgang/J
```

4. Format the J drive (there was some windows stuff on here for some reason)

```bash
>>  sudo apt-get install gparted
>>  sudo gparted #use the gui to format the 1.8 Tb drive
```

3. Configure /etc/fstab to mount at J.  Add the line:
```bash
/dev/sda1    /home/srgang/J    ext4    defaults 0 0
```

4. Configure /etc/samba/smb.conf.  Add the following to the end of the file
```bash
[J]
path = /home/srgang/J
valid users = srgang
read only = no
browsable = yes
writable = yes
```

5. Restart the samba server:
```bash
>> sudo /etc/init.d/samba restart
```

6. Now we should be serving the J drive over the network.  Lets configure some connections. 

On YeCookieMonster (ubuntu 18.04), add the following to /etc/fstab
```bash
//192.168.1.8/J /home/yelab/J cifs credentials=/home/yelab/.smbcredentials,file_mode=0777,dir_mode=0777 0 0
```

add the following to the .smbcredentials file

```bash
username=srgang
password=<usual with ! at end>
```

On YeOscarTheGrouch (Windows 10), add a .bat file on the desktop that executes the following command
```dos
net use J: \\192.168.1.8\J /user:srgang <usual password with !>
```

I also had to follow the instructions on [this page](https://tech.nicolonsky.ch/windows-10-1709-cannot-access-smb2-share-guest-access/) to get SMB to work in windows 10

**NOTE:** To set up a similar share on your own computer, you must replace "192.168.1.8" with "yeelmo" assuming that you are connecting through the JILA network rather than the Sesame Street network.  

7.  Set up automatic daily backup of J drive to Z drive on YeElmo.  Add the following line to crontab:

```bash
0 4 * * * rsync -ru --exclude=lost+found /home/srgang/J/ /home/srgang/yedata/SrE/backupJ/
```
This will write any changes in J to Z every day at 4 AM.