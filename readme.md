# Labrad_tools.test

To understand how to set up `labrad_tools`. 

## Log
Installing labrad manager. Use [scalalabrad](https://github.com/labrad/scalabrad)

I had to install Java8 to set `JAVA_HOME`.

Configuring node following [wiki](https://github.com/PickyPointer/SrE/wiki/Configuring-Labrad-Nodes) from Eric. Cloned it on this repository (`copy_SrE.wiki/`). `serial` server added.

Try to add `picoscope` server. Following [Picoscope in Labrad](https://github.com/PickyPointer/SrE/wiki/Picoscope-in-Labrad) section.
Install the [drivers](https://www.picotech.com/downloads/linux).
Change udev rules. For the picscope I have, `ATTRS{idVendor}=="0x0ce9", ATTRS{idProduct}=="0x0ce9", MODE="664", GROUP="pico", SYMLINK+="picoscope3403D"
`. This setting might not be necessary since we will read the serial number of the scope. 

```
sudo systemctl enable labrad-manager.service
sudo systemctl enable labrad-node.service
sudo systemctl enable labrad-web.service

```
Install `scalabrad-web`.
Following is required for autostart. `sudo visudo -f /etc/sudoers`
```
Defaults env_keep += "PYTHONPATH LABRADHOST LABRADNODE LABRADPASSWORD LABRAD_TLS"
```

Install lab modified version of `ps3000a.py`
In this case, the path is `/usr/local/lib/python3.10/dist-packages/picoscope`


## TODO

## Notes
- Installing `.tar.gz` files : `tar xzvf <file>`

## Environment
- Lenovo ThinkCentre M70q Gen 2
- Ubuntu 22.04.2 LTS
- python 3.10
- 

