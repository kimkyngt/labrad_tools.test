**Installing Picoscope on yecookiemonster**

First, I did the following (from [picotech website]( https://www.picotech.com/downloads/linux) ):
1. Add repository to the updater

`sudo bash -c 'echo "deb https://labs.picotech.com/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope.list'`

2. Import public key

`wget -O - https://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add -`

3. Update package manager cache

`sudo apt-get update` 

4. Install PicoScope

`sudo apt-get install picoscope`

Next I decided to update the udev rules so the picoscope is identified properly when it is plugged into the machine.  I assigned each picoscope a symbolic device name assuming that Labrad would need this device name to connect to the correct usb port.  Hard-coding a USB port number into code is a bad idea because it can change when he device is unplugged or when the computer is restarted.

Open the udev rule file:
`sudo gedit /etc/udev/rules.d/95-pico.rules`

Set the following udev rules:

`ATTRS{idVendor}=="0ce9", ATTRS{idProduct}=="1019", MODE="664", GROUP="pico", SYMLINK+="picoscope5000"`

`ATTRS{idVendor}=="0ce9", ATTRS{idProduct}=="1213", MODE="664", GROUP="pico", SYMLINK+="picoscope3000"`

Note that these are modified from the default udev rule that is set when the manufacturer package is installed:

`ATTRS{idVendor}=="0ce9", MODE="664", GROUP="pico"`

The default udev rule is generic does not specify the idProduct (ie which type of picoscope) so any picoscope will be identified, but one cannot immediately tell them apart from one another.  Unfortunately this means that if we purchase a different type of picoscope (say a picoscope 2000), it won't work until someone adds a new udev rule with the correct product ID.  To find the product ID:

`lsusb -v | less`

And scroll down until you find the usb entry for the picoscope.

Also if we purchase an additional picoscope of the same type (say another 3000 series) we'll need to add an additional attribute to the udev rule (the device serial number, for example) so we can tell them apart and specify different symlinks for each picoscope so Labrad can find both easily.

Now we should be able to see the picoscope symlinks show up in the devices folder.  To check:

`ls -l /dev | grep pico`

Finally, I installed the [pico-python](https://github.com/colinoflynn/pico-python) package for communicating with the picoscope though python.  Ross' code uses this package.

`sudo pip install picoscope`

Looking at the pico-python package, it appears that the code already has the functionality that it can look through all devices and connect to a device according to its serial number, so my udev rules might not be strictly necessary for interfacing with Labrad.  Still I generally think it's good practice to always specify device-specific udev rules.


**Configuring the Labrad picoscope server**

Ross seems to have hacked the pico-python package to add the functionality for searching for and identifying all picoscopes and returning their serial numbers.  This function is called when the labrad server is initiallized. Rather than hacking the yecookiemonster pico-python package, I decided to tweak the server code slightly.  It now opens a text file which contains the serial numbers of all picoscopes connected to the computer. 
**NOTE: this file needs to be updated when new picoscopes are added to the system.**  


