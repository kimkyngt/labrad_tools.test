# Windows 7:
1.  [Set environment variables](https://www.computerhope.com/issues/ch000549.htm) for Labrad.  Note: You may have to restart the computer for these changes to take effect.

LABRADNODE = yesr1 (for this example)

LABRADHOST = 192.168.1.8  (IP for yeelmo on sesame street network)

LABRADPASSWORD = usual with ! at end

LABRAD_TLS = off

2. Install pylabrad on yesr1:  pip install pylabrad

3. Clone the labrad_tools repo (on desktop of yesr1)

4. Add to python path: C:\users\Desktop\labrad_tools

5. For yesr1 we need the right version of pyserial (ver 2.7) for serial server: pip install pyserial==2.7

6. go to labrad_tools/batch -> start_servers.bat.  This will start the labrad node on yesr1.

7. Configure Labrad node through pylabrad connection in ipython:

```python
#Establish labrad connection
import labrad
cxn = labrad.connect()

#Go to yesr1 Node
r = cxn.registry
r.cd('Nodes')
r.cd('yesr1")

#Add labrad_tools to 'directories' so it can see the server code
r.set('directories', ['C:\Users\srgang\Desktop\labrad_tools'])
cxn.node_yesr1.refresh_servers()

#List available servers (to double-check that it worked)
cxn.node_yesr1.available_servers()

#Add any servers that we want to run automatically:  In this case the SerialServer hardware interface server
cxn.node_yesr1.autostart_add('serial')

#Call the autostart function if you want to run the server right now
cxn.node_yesr1.autostart()
```
Now the serial server will start automatically in the future when we execute the batch file in step 6.


# Ubuntu 18.04:

1. Go to systemd folder in labrad_tools and copy to system file directory:

cp -r labrad-node.service* /etc/systemd/system/

2. Edit the /etc/systemd/system/labrad-node.service.d/labrad-node.conf file to define environment variables
```bash
Environment="LABRADNODE = yecookiemonster" (for this example)
Environment="LABRADHOST=192.168.1.8"
Environment="LABRADPASSWORD = usual with ! at end"
Environment="LABRAD_TLS=off"
Environment="PYTHONPATH=/home/srgang/SrE/labrad_tools/"
```

3. If necessary edit /etc/systemd/system/labrad-node.service with the correct user, group name, and path to labrad-tools folder.

```bash
[Unit]
Description=labrad node
After=network-online.target

[Service]
Type=simple
User=<username>
Group=<groupname>
WorkingDirectory= </path/to/labrad_tools>
ExecStart=/usr/bin/python -m labrad.node
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

4. Start the labrad node:
sudo systemctl start labrad-node

5. Enable automatic starting of labrad node:
sudo systemctl enable labrad-node

6. Copy the labrad-node-journal script into labrad_tools/systemd/ folder (I will add this to the Sr1 Git Repo)

7. Launch the labrad-node-journal to print info from the labrad node.

8.  add the following to ~/.bashrc 

export LABRADNODE = yecookiemonster

export LABRADHOST = 192.168.1.8

export LABRADPASSWORD = usual with ! at end

export LABRAD_TLS = off

export PYTHONPATH=$PYTHONPATH:/path/to/labrad-tools/

9.  Configure Node through pylabrad (see step 7 in windows example)

10.  The commands at bootup will be executed as root, so the root account needs access to the environment variables we've defined.  Add the following to /etc/sudoers:

Defaults  env_reset

Defaults  env_keep += "PYTHONPATH LABRADHOST LABRADNODE LABRADPASSWORD LABRAD_TLS"

You must use the visudo command to edit your sudoers file.
