# Introduction

We use a software package called [_Labrad_tools_](https://github.com/yesrgang/labrad_tools) to control our experiment.  It is based off of [Labrad](https://github.com/labrad), a software suite designed to simplify communication with and control of experimental hardware over a lab network.  

As an introduction to _Labrad_tools_ this wiki page will walk through an example of a simple experiment running the software.  This walkthrough will be somewhat superficial for the sake of clarity.  Links to other wiki pages explaining the various aspects of _Labrad_tools_ in more detail will be provided when appropriate.

# Detailed Example

In this example, we will setup a simple experiment with the goal of performing a clock scan to scan out our line.  For this purpose, Labrad will only need to communicate with three hardware devices:

1. An RF source (DDS) for steering the clock laser frequency
2. A TTL box for controlling our shutters and triggering other hardware at specific times.
3. A picoscope for reading out the fluorescence signal during our excited state fraction measurement.

We will walk through how to configure and run the appropriate labrad servers using the _Labrad_tools_ package.  

## Experimental layout

[[images/LabradSchematic.png]]

A schematic for our setup is shown above.  For the purposes of demonstrating the functionality of the _Labrad_tools_ package, we've chosen to spread this very simple experiment across three different computers.  One machine, yecookiemonster, is hosting the Labrad Manager.  The Labrad Manager is not a part of _Labrad_tools_.  Rather, it is an integral part of Labrad itself.  First, Labrad was installed on yecookiemonster and the computer was configured to start the Labrad Manager at bootup.  For more details, see the wiki page:  [[Installing the labrad manager |Installing the labrad manager]].  Note that the DDS for steering our clock frequency is plugged into yecookiemonster.  We have an additional hardware computer yeelmo which is connected to our picoscope and the ttl sequencer box.  Finally we interface with the experiment using one of our data analysis computers, yebigbird.

Our experiment is controlled via a collection of Labrad servers running on all three machines.  The Labrad Manager orchestrates all communication between the various servers.  The _Labrad_tools_ package is written in python and communicates with the Labrad Manager using the [pylabrad](https://github.com/labrad/pylabrad) library.  The servers running on these machines are of the following types:

1.  HardwareInterfaceServer:  These servers handle low-level communication with specific types of experimental hardware.  If any computer on our experiment is connected to a specific class of device, its corresponding HardwareInterfaceServer must be running on that machine.  For example, if I were to add a DDS to the yebigbird machine, the serialServer HardwareInterfaceServer must be running on that machine in order for Labrad to be able to communicate with it.  

2.  DeviceServer:  These servers handle high-level communication with a specific class of devices.  Typically, these devices are grouped in terms of functionality rather than communication protocol.  For example, the rf DeviceServer handles communication with a variety of rf frequency sources using gpib, ethernet, and serial communication.  Because the hardware interface server methods are sufficiently generic the rf server can easily communicate with any rf device provided that it is told which Hardware interface server and device to talk to (more on this later).  

3. Conductor:  This is the single most important server.  It handles reading/writing values to all devices each experimental cycle.

We will now discuss each server class in turn and describe how they must be configured to run the desired hardware and experimental sequence.

### Aside: LabradServer Class in pylabrad

All of the server classes in _Labrad_tools_ inherit from the _LabradServer_ class in pylabrad.  An example template showing how to define a child class for _LabradServer_ lives [here](https://github.com/labrad/pylabrad/blob/master/labrad/servers/server_template.py). I've copied it below.  

```python
from labrad.server import LabradServer

class ServerTemplate(LabradServer):
    """Template for a python LabRAD server.
    This doc string will appear as descriptive help text when
    this server connects to LabRAD.
    """

    # the server name will identify this server in LabRAD
    # note that this name should match that given in the
    # .ini file for this server, if you want to use this
    # server with the node.
    name = 'Python Server Template'

    # Server startup and shutdown
    #
    # these functions are called after we first connect to
    # LabRAD and before disconnecting.  Here you should perform
    # any global initialization or cleanup.
    def initServer(self):
        """Initialize Server.
        Called after registering settings and creating a client
        connection to labrad, but before we start serving requests.
        """

    def stopServer(self):
        """Stop the server.
        Called when the server is shutting down, but before we have
        closed any client connections.  Perform any cleanup operations here.
        """

    # Context handling
    #
    # these functions are called to initialize and expire
    # context objects for requests.  The object c is a
    # dict-like object that you can use to store and data you
    # would like to have associated with the context.  This same
    # context object will get passed in to request handlers as well.
    def initContext(self, c):
        """Initialize a new context object."""
    def expireContext(self, c):
        """Expire Context.
        Called when a client which created a context disconnects,
        or when the client explicitly requests the expiration.
        Any cleanup operations on the context should be done here.
        """

    # Manager notifications
    #
    # These functions will be called in response to notifications
    # from the manager about events happening in the LabRAD system.
    # They let you respond to the connection and disconnection
    # of other servers.
    def serverConnected(self, ID, name):
        """This function will be called when a new server connects to LabRAD."""

    def serverDisconnected(self, ID, name):
        """This function will be called when a server disconnects from LabRAD."""


# create an instance of our server class
__server__ = ServerTemplate()

# this is some boilerplate code to run the
# server when this module is executed
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
```

The methods shown in this template class are generic methods in the _LabradServer_ class that we can override when defining the child class.  For most servers defined in _Labrad_tools_ only the initServer method is actually used.  This method is always called when the server is started and is intended to handle initialization tasks which are specific to the child class being defined.  Of course, we can define additional methods for the child class which are not included in the parent class.

At the bottom of this code are a few lines which first create an instance of the child class and then starts the server using labrad.util.runServer from pylabrad.  This establishes a connection with the Labrad Manager, runs the initialization methods in the parent class _LabradServer_, and finally runs the initServer method in the child class.

One last aspect of this template class is worth noting:  The context variable c.  Although the two methods for interacting with c shown in the template aren't used in _Labrad_tools_ the context variable c is itself heavily used.  **Ross: Could you add a bit more information about what c contains and when/where it is defined?**

## HardwareInterfaceServer
Now that we've introduced the layout of the experiment and the basic structure of our labrad servers, we will go through each class of server and explain their functionality.  

We begin with the hardware interface server class.  These servers handle low-level communication with specific classes of devices.  Each child class which inherits the HardwareInterfaceServer class essentially takes a python library for communicating with a type of hardware and creates a wrapper for using that communication library through Labrad.  For example, _serialServer_ is a class for communicating to serial devices through Labrad using the pySerial library.  The generic HardwareInterfaceServer class is included below.

```python
from labrad.server import LabradServer, setting

class InterfaceNotSelected(Exception):
    """ context has no selected interface for this server instance 
    
    If you have previously selected an interface, this server may have been 
    restarted and you must call "select_interface" again.
    """

class HardwareInterfaceServer(LabradServer):
    """ Template for hardware interface server """

    def initServer(self):
        self.interfaces = {}
        self.refresh_available_interfaces()

    def stopServer(self):
        """ notify connected device servers of closing connetion"""

    def refresh_available_interfaces(self):
        """ fill self.interfaces with available hardware """

    def call_if_available(self, f, c, *args, **kwargs):
        try:
            interface = self.get_interface(c)
            ans = getattr(interface, f)(*args, **kwargs)
            return ans
        except:
            self.refresh_available_interfaces()
            interface = self.get_interface(c)
            return getattr(interface, f)(*args, **kwargs)

    def get_interface(self, c):
        if 'address' not in c:
            raise InterfaceNotSelected
        if c['address'] not in self.interfaces.keys():
            self.refresh_available_interfaces()
            if c['address'] not in self.interfaces.keys():
                message = c['address'] + 'is unavailable'
                raise Exception(message)
        return self.interfaces[c['address']]

    @setting(0, returns='*s')
    def list_interfaces(self, c):
        """Get a list of available interfaces"""
        self.refresh_available_interfaces()
        return sorted(self.interfaces.keys())

    @setting(1, address='s', returns='s')
    def select_interface(self, c, address):
        """Select a specific interface"
        self.refresh_available_interfaces()
        if address not in self.interfaces:
            message = c['address'] + 'is unavailable'
            raise Exception(message)
        c['address'] = address
        return c['address'] 
```
Recall from the previous section that the initServer method is called after the server connects to the Labrad Manager.  The initServer method calls the refresh_available_interfaces method which determines what devices are connected to the computer running the server and loads these devices into a dict called interfaces.  Subsequently, other labrad servers can communicate with these devices.

Note that, for some of these methods, a decorator @setting appears before the method definition.  A method needs a @setting decorator to be accessible through Labrad over the network.  Each setting must be given a unique number which appears as its first argument.  Any child class defining additional @setting methods must choose different numbers from those that have already been assigned to methods in the parent class.  We will elaborate on these points further when we discuss the subclasses.

The list_interfaces and select_interface methods are available through Labrad.  The list_interfaces method returns a list of devices which the HardwareInterfaceServer is connected to.  The select_interface method establishes a connection to a specific hardware device.  This works by writing the device address to the context variable c.  Any other method in the parent or child class which passes c as an argument will subsequently know which device to talk to. 

The other important method here is call_if_available.  This method is our generic method for calling functions from the python library being used to talk to our experimental haradware with some built-in protections to make sure that the device is available for communication.  One line in call_if_available uses the getattr function which one may not be familiar with.  The line

```python
ans = getattr(interface, f)(*args, **kwargs)
```
should be read as 
```python
ans = interface.f(*args, **kwargs)
```

This allows us to call specific functions from the python communication library with the function name f passed as a string.  If one decides to input keyword arguments they must be specified as dict entries {paramater_name: paramater_value}.  

### SerialServer

In this example experiment we have a DDS board which is controlled by a microcontroller.  That microcontroller is connected to yecookiemonster over usb.  We must run an instance of the SerialServer class on yecookiemonster in order to be able to communicate with the microcontroller.  All communication is carried out using the pyserial library.  For the sake of brevity, I will not include the entire serialServer class in the text, but simply highlight a few methods.  First up are the refresh_available_interfaces and get_interface methods

```python
class SerialServer(HardwareInterfaceServer):
    """Provides access to hardware's serial interface """
    name = '%LABRADNODE%_serial'

    def refresh_available_interfaces(self):
        if sys.platform.startswith('win32'):
            addresses = ['COM{}'.format(i) for i in range(1, 30)]
        else:
            addresses = [cp[0] for cp in serial.tools.list_ports.comports()]
        
        for address in addresses:
            if address in self.interfaces.keys():
                try:
                    self.interfaces[address].isOpen()
                except:
                    print '{} unavailable'.format(address)
                    del self.interfaces[address]
            else:
                try:
                    ser = Serial(address)
                    ser.setTimeout(0)
                    ser.close()
                    self.interfaces[address] = ser
                    print '{} available'.format(address)
                except Exception, e:
                    pass
#                    print 'trouble with address {} ...'.format(address)
#                    print e
        
    def get_interface(self, c):
        interface = super(SerialServer, self).get_interface(c)
        if not interface.isOpen():
            interface.open()
            # for arduino, should require opt in somehow
            sleep(2)
        return interface
```
both of these methods override the versions in the HardwareInterfaceServer class.  The refresh_available_interfaces method first enumerates all available serial ports on the host computer and then verifies that it can connect with each serial device using the pySerial library.  The interfaces dict is populated with key:value where the key is the serial port and the value is a pySerial object.  The get_interface method opens the a serial connection with the hardware device that was selected using the select_interface method in the parent class (see the previous section).

Most of the remaining methods in this class are @setting methods for sending specific serial commands to the device.  I won't describe all of the methods in detail.  Instead I'll refer you to a wiki page which provides additional documentation for this class: [[SerialServer |SerialServer]]. Let's now take a look at the first @setting method in this class to get an idea of how they operate.

```python
    @setting(2, returns='b')
    def disconnect(self, c):
        self.refresh_available_interfaces()
        if c['address'] not in self.interfaces:
            raise Exception(c['address'] + 'is unavailable')
        interface = self.get_interface(c)
        interface.close()
        del c['address']
        return True

    @setting(3, baudrate='w', returns='w')
    def baudrate(self, c, baudrate=None):
        if baudrate is not None:
            self.call_if_available('setBaudrate', c, baudrate)
        baudrate = self.call_if_available('getBaudrate', c)
        return baudrate
```
 
Note that the @setting index here starts with 2.  This is because index 0 and 1 are already defined in the parent class and we don't want to overwrite them.  It is OK to skip index numbers, but one should never use the same index twice.  The disconnect method is straightforward.  It grabs the selected interface stored in c and closes its serial connection.  The baudrate method uses the pySerial function setBaudrate through the call_if_available method in the HardwareInterfaceServer class to set the baudrate of the serial device.

The remaining two hardware interface servers used in this experiment are very similar to the SerialServer.  We will provide some quick facts about both but refer the reader to separate wiki pages for a detailed description of each class.

### PicoscopeServer

The PicoscopeServer uses the _picoscope_ python library provided by picotech.  For information on installing this library see this wiki page: [[Picoscope in Labrad |Picoscope in Labrad]].  The @settings functions in this class are simply wrappers for the various functions in the _picoscope_ library.  For more details on the member functions in this class see the wiki page [[PicoscopeServer|PicoscopeServer]].

### OKFPGAServer

Fill this in later

### Example: Talking to a picoscope over Labrad

In this section, we'll show how to communicate with a picoscope through its HardwareInterfaceServer.  During normal experimental operation, one probably wouldn't access the low-level communication servers directly.  Nonetheless it is a useful exercise for familiarizing onesself with Labrad.  The first step is to start the PicoscopeServer on the computer that is connected to the picoscope.  On yeelmo, navigate to the labrad_tools/picoscope_server/ directory then start the server:

`python picoscope_server.py` 

In the future we can configure yeelmo to start its labrad servers automatically.  See the wiki page [[Configuring Labrad Nodes|Configuring Labrad Nodes]] for details on how to do this.  Now that the server is running on yeelmo and the Labrad Manager is running on yecookiemonster, we should be able to talk to our device from yebigbird provided that it has been set up to talk to the correct Labrad Manager (see wiki page [[Configuring a new computer|Configuring a new computer]]).  We begin by opening a python terminal on yebigbird, importing the pylabrad library, and opening a connection to the Labrad Manager over the network.

```python
> import labrad
> cxn = labrad.connect()
```
Next, we'll select the desired piece of hardware. We're going to talk to a picoscope with serial number = "FP648/023".  

```python
> cxn.yeelmo_picoscope.list_interfaces()
['FP648/023']
> cxn.yeelmo_picoscope.select_interface('FP648/023')
```
Note that in order to call member functions from the picoscope server, we needed to tell the Labrad Manager which server we wanted to talk to.  The name of the server is stored in PicoscopeServer.name.  From picoscope_server.py we find the naming convention specified in the server class definition:

```python
class PicoscopeServer(HardwareInterfaceServer):
    """Provides access to picoscopes """
    name = '%LABRADNODE%_picoscope'
```
Here, %LABRADNODE% just the computer name on which the server is running: yeelmo.  Now that we've selected the picoscope we wish to communicate with we can send it a command.  First, let's configure channel A of our picoscope to be AC coupled with a voltage range of 1V.  

```python
> cxn.yeelmo_picoscope.set_channel('A','AC',1.0,1,True)
```
Now let's configure it to take 100 seconds of data at a 1kHz sampling rate

```python
> cxn.yeelmo_picoscope.set_sampling_frequency(100,1000)
```
Let's take some data
```python
> cxn.yeelmo_picoscope.run_block()
```

When you are entering these method calls don't include keywords.  For example cxn.yeelmo_picoscope.set_sampling_frequency(duration = 100,frequency= 1000) will not work.  This seems to be a bug in _labrad_tools_

## DeviceServer class

Now that we understand and can run our hardware interface servers we will now turn our attention to the device servers.  As discussed previously, the device servers handle high-level communication with our hardware devices.  They communicate with the appropriate hardware interface servers as needed.

We'll begin by looking at the DeviceServer class. Like HardwareInterfaceServer, DeviceServer inherits the LabradServer class and is the parent class for all of our device servers.  Let's go through the code piece-by-piece to understand how it works.  we'll start with the first three methods

```python
class DeviceServer(LabradServer):
    devices = {}
    
    @inlineCallbacks
    def initServer(self):
        for device in self.get_configured_devices():
            if getattr(device, 'autostart'):
                yield self.initialize_device(device.name)

    def get_configured_devices(self):
        assert os.path.exists('./devices/')
        device_names = [name 
            for _, name, ispkg in pkgutil.iter_modules(['./devices/'])
            if not ispkg
            ]
        configured_devices = []
        for device_name in device_names:
            device = import_device(device_name)
            if device:
                configured_devices.append(device)
        return configured_devices
    
    @inlineCallbacks 
    def initialize_device(self, device_name):
        if device_name in self.devices:
            message = 'device {} is already active'.format(device_name)
            raise Exception(message)
        try:
            device_class = import_device(device_name)
            device = device_class()
            device.device_server = self
            device.device_server_name = self.name
            yield device.initialize()
            self.devices[device_name] = device
        except Exception as e:
            print e
            print 'unable to initialize device {}'.format(device_name)
```
As is the case for all classes inheriting the LabradServer class, the initServer method is called when the server is started.  initServer calls the _get_configured_devices_ method which looks at the python files in the ./devices subfolder and reads off the name of each device, which is simply given by the file name associated with the device class.

For all devices where device.autoload = True, the device classes are imported, an instance of the class is created and then initialized, and the device objects are loaded into the self.devices dictionary with entries of the form {device_name: deviceObject}.  We will discuss the Device objects in more detail momentarily. 

We note that there is a new decorator being used: @inlineCallbacks.  This is required for a method to be available over the network.  This is necessary for the initServer and initialize_device methods because devices typically need to establish a network connection to the Labrad Manager when they are initialized.  **Ross: is this the correct explanation?**

```python
    @inlineCallbacks 
    def terminate_device(self, device_name):
        if device_name not in self.devices:
            message = 'device {} is not active'.format(device_name)
            raise Exception(message)
        try:
            device = self.devices.pop(device_name)
            yield device.terminate()
        except Exception as e:
            print e
            print 'unable to cleanly terminate device {}'.format(device.name)
        finally:
            del device

    def get_selected_device(self, c):
        device_name = c.get('device_name')
        if device_name is None:
            raise Exception('select a device first')
        return self.devices[device_name]
    
    @setting(0, returns='s')
    def list_devices(self, c):
        """ list available devices
        
        Args:
            None
        Returns:
            json dumped dict
            {
                'active': active_devices,et_configured_devices
                'configured': configured_devices,
            }
            where active_devices is list of names of running devices
            and configured_devices is list of names of devices configured in './devices'
        """
        active_device_names = self.devices.keys()
        configured_devices = self.get_configured_devices()
        configured_device_names = [device.name for device in configured_devices]
        response = {
            'active': active_device_names,
            'configured': configured_device_names,
            }
        return json.dumps(response)

    @setting(1, device_name='s', returns=['s', ''])
    def select_device(self, c, device_name):
        if device_name not in self.devices.keys():
            yield self.initialize_device(device_name)

        if device_name in self.devices.keys():
            c['device_name'] = device_name
            device = self.get_selected_device(c)
            device_info = {x: getattr(device, x) for x in dir(device) if x[0] != '_'}
            # ignore if cannot serialise
            device_info = json.loads(json.dumps(device_info, default=lambda x: None))
            device_info = {k: v for k, v in device_info.items() if v is not None}
            returnValue(json.dumps(device_info))
        else:
            message = 'Device {} could not be initialized. See server log for details.'.format(device_name)
            raise Exception(message)
    
    @setting(2)
    def send_update(self, c):
        device = self.get_selected_device(c)
        update = {c['device_name']: {p: getattr(device, p) 
                  for p in device.update_parameters}}
        yield self.update(json.dumps(update))

    @setting(3, device_name='s')
    def reload_device(self, c, device_name=None):
        if device_name is None:
            device_name = c.get('device_name')
        if device_name in self.devices:
            yield self.terminate_device(device_name)
        yield self.initialize_device(device_name)

```

The remaining methods are just helper functions for interfacing with the device objects.  They are very similar to those found in the HardwareInterfaceServer class.  Again, any methods with the @settings decorator are available through Labrad.  Like select_interface in HardwareInterfaceServer, the select_device method is once again responsible for setting the context variable c.  This time it loads the selected Device object into a dict {device_name:device} which is passed to all other helper functions so they know which device to communicate with.

To complete our discussion of the DeviceServer, we will also introduce the generic Device class.  We will use this template class to define device classes for each type of hardware we want to control with our device servers.

```python
def import_device(device_name):
    try:
        module_path = 'devices.{}'.format(device_name)
        device_class_name = '__device__'
        module = __import__(module_path, fromlist=[device_class_name])
        reload(module)
        device = getattr(module, device_class_name)
        device.name = device_name
        return device
    except Exception as e:
        print e
        print 'invalid device in ./devices/{}'.format(device_name)

class Device(object):
    autostart = False
    update_parameters = []
    
    def initialize(self):
        pass

    def terminate(self):
        pass

    @inlineCallbacks
    def connect_labrad(self):
        connection_name = '{} - {}'.format(self.device_server_name, self.name)
        self.cxn = yield connectAsync(name=connection_name)
```

The helper function import_device loads the device module in the ./devices/ subfolder and is used by DeviceServer.initialize_device.  Here the Device class is left completely generic other than a fairly straightforward method for connecting the device to the Labrad Manager.  

Once again we include the decorator @inlineCallbacks for Device.connect_labrad because we are using the method twisted.connectAsync.  This decorator is typically needed for function calls from the [twisted](https://github.com/twisted/twisted) library.  Since the device is initialized by DeviceServer.initialize_device which in turn is called by DeviceServer.initServer, both of those methods also require the @inlineCallbacks decorator.

Now that we've introduced the parent classes, we'll now discuss the device servers used in this experiment and their corresponding device classes.

## rfServer and the AD9854 device

To steer our clock laser frequency, we need to be able to adjust the frequency of the RF source for the clock laser AOM.  For this example, we'd like to communicate with an AD9854 DDS.  The serialServer can coordinate sending serial commands to the Arduino which controls the DDS, but we need to define high level functions which can convert human-readable parameters into serial commands.  For this, we will need to define a device class AD9854 with methods that convert real word parameters into serial commands for the Arduino.  We will then create a child class of AD9854 called clockLaser which simply inherits all methods from AD9854 and specifies which server and USB port this particular dds is connected to.  Let's take a look at the AD9854 class.

```python
class AD9854(Device):
    serial_server_name = None
    serial_address = None
    serial_timeout = 0.5
    serial_baudrate = 4800
    
    address = None

    sysclk = 300e6
    freg = int(0x02)
    areg = int(0x08)
    
    state = True
    
    amplitude = None
    default_amplitude = 1
    amplitude_range = (0, 1)
    
    frequency = None
    default_frequency = 80e6
    frequency_range=(1e3, 140e6)

    update_parameters = ['state', 'frequency', 'amplitude']

    def make_ftw(self, frequency):
        ftw = hex(int(frequency * 2.**32 / self.sysclk))[2:].zfill(8) # 32-bit dac
        return [int('0x' + ftw[i:i+2], 0) for i in range(0, 8, 2)]

    def make_atw(self, amplitude):
        atw =  hex(int(amplitude * (2**12 - 1)))[2:].zfill(4)
        return [int('0x'+atw[i:i+2], 0) for i in range(0, 4, 2)] + [0, 0]

    @inlineCallbacks
    def initialize(self):
        yield self.connect_labrad()
        self.serial_server = yield self.cxn[self.serial_server_name]
        yield self.serial_server.select_interface(self.serial_address)
#        yield sleep(2)
        yield self.serial_server.timeout(self.serial_timeout)
        yield self.serial_server.baudrate(self.serial_baudrate)

        yield self.set_frequency(self.default_frequency)
        yield self.set_amplitude(self.default_amplitude)
    
    def set_state(self, state):
        pass

    def get_state(self):
        return True

    @inlineCallbacks
    def set_frequency(self, frequency):
        ftw = self.make_ftw(frequency)
        for b in get_instruction_set(self.subaddress, self.freg, ftw):
            yield self.serial_server.write(b)
        ans = yield self.serial_server.read_line()
        if ans != 'Roger that!':
            message = 'Error writing {} frequency'.format(self.name)
            #raise Exception(message)
            print ans
            print messageclass AD9854(Device):
    serial_server_name = None
    serial_address = None
    serial_timeout = 0.5

        else:
            print ans
        self.frequency = frequency

    def get_frequency(self):
        return self.frequency
        
    @inlineCallbacks
    def set_amplitude(self, amplitude):
        atw = self.make_atw(amplitude)
        for b in get_instruction_set(self.subaddress, self.areg, atw):
            yield self.serial_server.write(b)
        ans = yield self.serial_server.read_line()
        if ans != 'Roger that!':
            message = 'Error writing {} amplitude'.format(self.name)
#            raise Exception(message)
            print ans
            print message
        else:
            print ans
        self.amplitude = amplitude

    def get_amplitude(self):
        return self.amplitude
```

At the beginning of the class definition, a series of device parameters are set.  Note that the instance-specific parameters self.serial_server and self.serial_address are left generic.  Those will be set in the clockLaser class.  The remaining parameters are common to all AD9854 DDS boards.  The first two methods make_ftw and make_atw convert the desired frequency and amplitude values into bit strings.  The remaining methods are for setting/getting parameters of the AD9854.  They are intended to be called through the rfServer.  We'll look into this more momentarily.  They call a helper function named get_instruction_set which embeds the bit strings within serial commands that are sent to the serialServer.

Next we create a child class that contains specific values for self.serial_server and self.serial_address and self.subaddress.  It also specifies a name for the device class which is stored in the `__device__` variable.  The device name is simply given by the name of the python file containing the definition of the child class.

```python
from devices.ad9854.ad9854 import AD9854

class clockLaser(AD9854):
    autostart = True
    serial_server_name = "yecookiemonster_serial"
    serial_address = "/dev/ttyACM0"
    subaddress = 0

    default_frequency = 125e6

__device__ = clockLaser
```

Finally, we'll look at the rfServer.  All the rfServer code really does is create wrappers for the get_ and set_ methods of whatever device we've selected with the rfServer.get_selected_device method.  This allows the user (or the Conductor server) to read/change settings of a given device through the rfServer without having to connect to the device directly.  
```python
from server_tools.device_server import DeviceServer
from server_tools.decorators import quickSetting

UPDATE_ID = 698034

class RFServer(DeviceServer):
    """ Provides basic control for RF sources """
    update = Signal(UPDATE_ID, 'signal: update', 's')
    name = 'rf'

    @quickSetting(10, 'b')
    def state(self, c, state=None):
        """ get or change state """

    @quickSetting(11, 'v')
    def frequency(self, c, frequency=None):
        """ get or change frequency """

    @quickSetting(12, 'v')
    def amplitude(self, c, amplitude=None):
        """ get or change amplitude """

    @quickSetting(13, 'v')
    def ramprate(self, c, ramprate=None):
        """ get or change ramprate """
    
    @quickSetting(14, 'v')
    def offset(self, c, offset=None):
        """ get or change offset """
    
    @setting(17, x='v', y='v', z='i')
    def linear_ramp(self, c, x=None, y=None, z=None):
        device = self.get_selected_device(c)
        yield device.set_linear_ramp(x, y, z)
```

At first glance, most of these methods don't actually appear to do anything.  The actual code is buried in the  @quickSetting decorator. This decorator creates a wrapper for the corresponding device method.  As an example, if we've called rfServer.select_device("clockLaser") and then call rfServer.frequency() it will create a wrapper that calls clockLaser.get_frequency().  The appropriate @settings decorator will be added to the wrapper so the method is available through Labrad.  If we instead call rfServer.frequency(1000), it will call the method clockLaser.set_frequency(1000).  Finally, if we call rfServer.offset() it will throw an exception because the clockLaser object doesn't have a get_offset method defined.  The code for the @quickSetting decorator lives in labrad_tools/server_tools/decorators.py file.

There's two more things to note about this class definition.  As was done for the HardwareInterfaceServers, a server name is specified.  When calling methods through a labrad connection, we must specify the name of the server.  However, unlike the HardwareInterfaceServers, we don't need to specify a host computer name.  This is because we only need one rfServer running for the entire experiment to manage all rf devices.  Therefore, if we want to set the frequency of the clock laser to 1 kHz:

```python
> import labrad
> cxn = labrad.connect()
> cxn.rf.select_device("clockLaser")
> cxn.rf.frequency(1000)
```

One new thing here is the rfServer.update member.  We won't elaborate on this for now but this class member will be important when we discuss the Conductor server later.

## PMTServer and picoscope device

Next up is the PMT server.  We will be reading out our excited state fraction by looking at the PMT signal for in the ground state fluorescence, excited state fluorescence, and the background.  We'll be recording our signal with the picoscope, so we want to set it up to grab a PMT trace during each of the three PMT measurements.  Recall that the PicoscopeServer hardware interface server is a wrapper for the picotech python library which is already fairly high level.  This means that we won't have to do nearly as much work to put the commands in the proper format for the hardware interface server.  Therefore, the device class for the picoscope is much simpler than the AD9845 class:

```python
class Picoscope(Device):
    picoscope_server_name = None
    picoscope_serial_number = None
    picoscope_duration = None
    picoscope_frequency = None
    picoscope_n_capture = None
    picoscope_trigger_threshold = None # [V]
    picoscope_timeout = None # [ms]

    records = {}
    record_names = deque([])
    max_records = 100
    
    @inlineCallbacks
    def initialize(self):
        yield self.connect_labrad()
        self.picoscope_server = yield self.cxn[self.picoscope_server_name]
        yield self.picoscope_server.select_interface(self.picoscope_serial_number)
        for channel, settings in self.picoscope_channel_settings.items():
            yield self.picoscope_server.set_channel(channel, settings['coupling'], 
                settings['voltage_range'], settings['attenuation'], settings['enabled'])
        
        yield self.picoscope_server.set_sampling_frequency(self.picoscope_duration, 
            self.picoscope_frequency)
        yield self.picoscope_server.set_simple_trigger('External', 
            self.picoscope_trigger_threshold, self.picoscope_timeout)
        _ = yield self.picoscope_server.memory_segments(self.picoscope_n_capture)
        yield self.picoscope_server.set_no_of_captures(self.picoscope_n_capture)

    @inlineCallbacks
    def record(self, data_path):
        yield None

    @inlineCallbacks
    def retrive(self, record_name, process_name):
        yield None
```

Basically this class only contains some parameters for the picoscope, an initialization method which writes these parameters to the device, and methods for saving/loading traces.  The specific parameters and more sophistocated methods are contained in the child class BluePMT:

```python
import json
import h5py
import numpy as np
import os
from scipy.optimize import curve_fit
import time

from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import returnValue
from twisted.internet.reactor import callInThread

from devices.picoscope.picoscope import Picoscope

#def fit_function(x, a, b):
#    T0 = -2e1
#    TAU1 = 6.5e3
#    TAU2 = 9.5e1
#    return a * (np.exp(-(x-T0)/TAU1) - np.exp(-(x-T0)/TAU2)) + b
#

TAU = 2.3e4
def fit_function(x, a):
    return a * np.exp(-x / TAU)

class BluePMT(Picoscope):
    autostart = False
    picoscope_server_name = 'yeelmo_picoscope'
    picoscope_serial_number = 'DY149/147'
    picoscope_duration = 2e-3
    picoscope_frequency = 100e6
    picoscope_n_capture = 3
    picoscope_trigger_threshold = 2 # [V]
    picoscope_timeout = -1 # [ms]

    picoscope_channel_settings = {
        'A': {
            'coupling': 'DC',
            'voltage_range': 10.0,
            'attenuation': 1,
            'enabled': True,
            },
        'B': {
            'coupling': 'DC',
            'voltage_range': 10.0,
            'attenuation': 1,
            'enabled': False,
            },
        'C': {
            'coupling': 'DC',
            'voltage_range': 10.0,
            'attenuation': 1,
            'enabled': False,
            },
        'D': {
            'coupling': 'DC',
            'voltage_range': 10.0,
            'attenuation': 1,
            'enabled': False,
            },
        }

    data_format = {
        'A': {
            'gnd': 0,
            'exc': 1,
            'bac': 2,
            },
        }

    p0 = [1]


    @inlineCallbacks
    def record(self, data_path):
        self.recording_name = data_path
        yield self.picoscope_server.run_block()
        callInThread(self.do_record_data, data_path)
#        yield self.do_record_data(data_path)
    
    @inlineCallbacks
    def do_record_data(self, data_path):
        raw_data_json = yield self.picoscope_server.get_data(json.dumps(self.data_format), True)
        raw_data = json.loads(raw_data_json)["A"]
        raw_sums = {label: sum(raw_counts) for label, raw_counts in raw_data.items()}
        raw_fits = {}

        b = np.mean(raw_data['bac'])
        for label, raw_counts in raw_data.items():
            counts = np.array(raw_counts)[500:] - b
            popt, pcov = curve_fit(fit_function, range(len(counts)), counts, p0=self.p0)
            raw_fits[label] = popt[0]

        tot_sum = raw_sums['gnd'] + raw_sums['exc'] - 2 * raw_sums['bac']
        frac_sum = (raw_sums['exc'] - raw_sums['bac']) / tot_sum
        tot_fit = raw_fits['gnd'] + raw_fits['exc'] - 2 * raw_fits['bac']
        frac_fit = (raw_fits['exc'] - raw_fits['bac']) / tot_fit

        processed_data = {
            'frac_sum': frac_sum,
            'tot_sum': tot_sum,
            'frac_fit': frac_fit,
            'tot_fit': tot_fit,
            }

        data_directory = os.path.dirname(data_path) 
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)
    
        print "saving processed data to {}".format(data_path)

        json_path = data_path + '.json'
        if os.path.exists(json_path):
            print 'not saving data to {}. file already exists'.format(json_path)
        else:
            with open(data_path + '.json', 'w') as outfile:
                json.dump(processed_data, outfile, default=lambda x: x.tolist())
        
        h5py_path = data_path + '.hdf5'
        if os.path.exists(h5py_path):
            print 'not saving data to {}. file already exists'.format(h5py_path)
        else:
            with h5py.File(h5py_path) as h5f:
                for k, v in raw_data.items():
                    h5f.create_dataset(k, data=np.array(v), compression='gzip')
        
        """ temporairly store data """
        if len(self.record_names) > self.max_records:
            oldest_name = self.record_names.popleft()
            if oldest_name not in self.record_names:
                _ = self.records.pop(oldest_name)
        self.record_names.append(data_path)
        self.records[data_path] = processed_data

        yield self.device_server.update(self.name)
    
    @inlineCallbacks
    def retrive(self, record_name):
        yield None
        if type(record_name).__name__ == 'int':
            record_name = self.record_names[record_name]
        if record_name not in self.records:
            message = 'cannot locate record: {}'.format(record_name)
            raise Exception(message)
        record = self.records[record_name]
        record['record_name'] = record_name
        returnValue(record)

__device__ = BluePMT
```
This child class defines the desired parameters for the picoscope.  The record and retrieve methods have been altered to be compatible with the data format and experimental sequence we'd like to use for our state readout traces.  The do_record_data method is responsible for grabbing the data from the scope, fitting the exponential fluorescence traces, calculating the excited state fraction and saving the processed data.  Finally, we look at the PMTServer device server:
```python
UPDATE_ID = 64883241

class PMTServer(DeviceServer):
    update = Signal(UPDATE_ID, 'signal: update', 's')
    name = 'pmt'

    @setting(11, record_name='s', returns='b')
    def record(self, c, record_name):
        device = self.get_selected_device(c)
        yield device.record(record_name)
        returnValue(True)
    
    @setting(12, record_name=['s', 'i'], returns='s')
    def retrive(self, c, record_name):
        device = self.get_selected_device(c)
        data = yield device.retrive(record_name)
        returnValue(json.dumps(data))
```
This simply creates Labrad compatible wrappers for the record and retrieve methods for the selected device.

## SequencerServer and the yesr_digital_board device

The SequencerServer is the device server for controlling our TTL box and DAC channels.  In this example experiment, we require a TTL box to open/close our shutters, trigger our picoscope and other experimental hardware, and turn on/off our MOT and bias coils (I'm ignoring any DAC controlled current ramps for the sake of simplicity).  We begin by considering the yesr_digital_board device.  The purpose of this device class is to manage the okfpga which controls the 64 TTL output channels for our TTL box.  This class will contain a list of channel objects for each TTL output.  The channel objects are defined as follows:

```python
class DigitalChannel(object):
    channel_type = 'digital'

    def __init__(self, loc=None, name=None, mode='auto', manual_output=False,
            invert=False):
        self.loc = loc
        self.name = str(name)
        self.mode = str(mode)
        self.manual_output = bool(manual_output)
        self.invert = bool(invert)

    def set_board(self, board):
        self.board = board
        row, column = self.loc
        self.board_loc = str(row) + str(column).zfill(2)
        self.key = self.name + '@' + self.board_loc
   
    @inlineCallbacks
    def set_mode(self, mode):
        if mode not in ('auto', 'manual'):
            message = 'channel mode {} not valid'.format(mode)
            raise Exception(message)
        self.mode = mode
        yield self.board.write_channel_modes()

    @inlineCallbacks
    def set_manual_output(self, state):
        self.manual_output = bool(state)
        yield self.board.write_channel_manual_outputs()
    
    def set_sequence(self, sequence):
        self.sequence = sequence
    
    def channel_info(self):
        device_info = {x: getattr(self, x) for x in dir(self) if x[0] != '_'}
        device_info = json.loads(json.dumps(device_info, default=lambda x: None))
        device_info = {k: v for k, v in device_info.items() if v is not None}
        return device_info
```
When initiallized, each channel is given a human-readable name and a location corresponding to an output on the ttl box.  For example, we might choose to use the third channel in row A for opening our polarizing beam shutter.  We would set self.name = "Polarizing Shutter" and self.loc = A2, and the set_board method would set self.key = "Polarizing Shutter@A2".  This "name@location" convention will be used by both the conductor and sequencer servers to refer to specific digital output channels.  Each channel can be switched between two modes using the set_mode method.  In "auto" mode, the channel output will simply follow our pre-defined sequence set with the set_sequence method (We'll elaborate on this more when we discuss the conductor server and the sequencer gui client), while in "manual" mode, the user can manually turn the channel on/off using the sequencer gui client (which calls the set_manual_output method).   

The yesr_digital_device class then contains methods for interfacing with these channel objects and for writing the channel values to the okfpga via the OKFPGAServer hardware interface server:

```python
T_TRIG = 10e-6

T_END = 10e-3 
T_WAIT_TRIGGER = 42.94967294 # (2**31 - 1) / clk

TRIGGER_CHANNEL = 'Trigger@D15'


class YeSrDigitalBoard(Device):
    sequencer_type = 'digital'

    okfpga_server_name = None
    okfpga_device_id = None

    channels = None
        
#    bitfile = 'digital_sequencer.bit'
#    bitfile = 'digital_sequencer-v2.bit'
    bitfile = 'digital_sequencer-v2b.bit'
    mode_ints = {'idle': 0, 'load': 1, 'run': 2}
    mode_wire = 0x00
    sequence_pipe = 0x80
    channel_mode_wires = [0x01, 0x03, 0x05, 0x07]
    state_invert_wires = [0x02, 0x04, 0x06, 0x08]
    clk = 50e6
    mode = 'idle'
    
    sequence_bytes = None

    @inlineCallbacks
    def initialize(self):
        self.mode = 'idle'
        assert len(self.channels) == 64
        for channel in self.channels:
            channel.set_board(self)
        
        yield self.connect_labrad()
        self.okfpga_server = yield self.cxn[self.okfpga_server_name]
        yield self.okfpga_server.select_interface(self.okfpga_device_id)

        yield self.okfpga_server.program_bitfile(self.bitfile)
        yield self.write_channel_modes()
        yield self.write_channel_manual_outputs()

    @inlineCallbacks
    def set_mode(self, mode):
        mode_int = self.mode_ints[mode]
        yield self.okfpga_server.set_wire_in(self.mode_wire, mode_int)
        yield self.okfpga_server.update_wire_ins()
        self.mode = mode

#    @inlineCallbacks
#    def program_sequence(self, sequence):
#        sequence_bytes = self.make_sequence_bytes(sequence)
#        yield self.set_mode('idle')
#        yield self.set_mode('load')
#        yield self.okfpga_server.write_to_pipe_in(self.sequence_pipe, json.dumps(sequence_bytes))
#        yield self.set_mode('idle')
    @inlineCallbacks
    def program_sequence(self, sequence):
        sequence_bytes = self.make_sequence_bytes(sequence)
        yield self.set_mode('idle')
        if sequence_bytes != self.sequence_bytes:
            yield self.set_mode('load')
            yield self.okfpga_server.write_to_pipe_in(self.sequence_pipe, json.dumps(sequence_bytes))
            yield self.set_mode('idle')
        self.sequence_bytes = sequence_bytes


    @inlineCallbacks
    def start_sequence(self):
        yield self.set_mode('run')

    def make_sequence_bytes(self, sequence):
        # make sure trigger happens on first run
        for c in self.channels:
            s = {'dt': T_TRIG, 'out': sequence[c.key][0]['out']}
            sequence[c.key].insert(0, s)

        # trigger other boards
        for s in sequence[TRIGGER_CHANNEL]:
            if s['dt'] >= (2**31 - 2) / self.clk:
                s['out'] = True
            else:
                s['out'] = False
        sequence[TRIGGER_CHANNEL][0]['out'] = True

        # allow for analog's ramp to zero, last item will not be written
        sequence[TRIGGER_CHANNEL].append({'dt': T_END, 'out': True})

        for c in self.channels:
            total_ticks = 0
            for s in sequence[c.key]:
                dt = time_to_ticks(self.clk, s['dt'])
                s.update({'dt': dt, 't': total_ticks})
                total_ticks += dt

        # each sequence point updates all outs for some number of clock ticks
        # since some channels may have different 'dt's, every time any channel 
        # changes state we need to write all channel outs.
        t_ = sorted(list(set([s['t'] for c in self.channels 
                                     for s in sequence[c.key]])))
        dt_ = [t_[i+1] - t_[i] for i in range(len(t_)-1)] + [time_to_ticks(self.clk, T_END)]

        programmable_sequence = [(dt, [get_output(sequence[c.key], t) 
                for c in self.channels])
                for dt, t in zip(dt_, t_)]
        
        sequence_bytes = []
        for t, l in programmable_sequence:
            # each point in sequence specifies all 64 logic outs with 64 bit number
            # e.g. all off is 0...0, channel 1 on is 10...0
            sequence_bytes += list([sum([2**j for j, b in enumerate(l[i:i+8]) if b]) 
                    for i in range(0, 64, 8)])
            # time to keep these outs is 32 bit number in units of clk ticks
            sequence_bytes += list([int(eval(hex(t)) >> i & 0xff) 
                    for i in range(0, 32, 8)])
        sequence_bytes += [0]*24
        return sequence_bytes
    
    @inlineCallbacks
    def write_channel_modes(self):
        cm_list = [c.mode for c in self.channels]
        values = [sum([2**j for j, m in enumerate(cm_list[i:i+16]) 
                if m == 'manual']) for i in range(0, 64, 16)]
        for value, wire in zip(values, self.channel_mode_wires):
            yield self.okfpga_server.set_wire_in(wire, value)
        yield self.okfpga_server.update_wire_ins()
        yield self.write_channel_manual_outputs()
   
    @inlineCallbacks
    def write_channel_manual_outputs(self): 
        cm_list = [c.mode for c in self.channels]
        cs_list = [c.manual_output for c in self.channels]
        ci_list = [c.invert for c in self.channels]
        values = [sum([2**j for j, (m, s, i) in enumerate(zip(
                cm_list[i:i+16], cs_list[i:i+16], ci_list[i:i+16]))
                if (m=='manual' and s!=i) or (m=='auto' and i==True)]) 
                for i in range(0, 64, 16)]
        for value, wire in zip(values, self.state_invert_wires):
            yield self.okfpga_server.set_wire_in(wire, value)
        yield self.okfpga_server.update_wire_ins()
```

When the device is first loaded, the initialize method is called.  This begins by iterating through all of the channels specified in self.channels and initializing the channels using the DigitalChannel.set_board method which defines the channel name and location.  Next, a connection is made to the okfpga hardware interface server and the bitfile is loaded on the fpga controlling the TTL box.  Finally the channel modes ("auto" or "manual") and their corresponding manual output values (for channels in "manual" mode) are written to the fpga

The bitfile is written in VHDL and its source code can be found in [Ross's VHDL repository](https://github.com/yesrgang/VHDL).  This tutorial won't explain the VHDL program in detail, but lets quickly go over a few key features that are important for understanding the associated _labrad_tools_ code.  First of all, we can set values for a few important gates by using the OKFPGAserver.set_wire_in to set values for their corresponding wire registers.  These registers and their functionality are as follows.

1.  self.mode_wire: This register specifies the operating mode of the fpga code.  If set to 0, the fpga is in 'idle' mode.  We set this register to 1 or 'load' mode when we want to upload a new sequence to the device.  When we want to execute the experimental sequence this register is set to 2 or 'run' mode
2.  self.channel_mode_wires:  Each of these four registers is assigned a 16-bit string which defines the operating mode ('auto' or 'manual') for 16 TTL output channels.
3.  self.state_invert_wires:  Each of these four registers is assigned a 16-bit string which specifies whether or not the logic is inverted for 16 TTL output channels.

The VHDL program also allows the user to program a sequence for each channel (when in 'auto' mode) using a pipe.  The sequence specifies what values the TTL outputs should have at specific times during one run of the experimental sequence.

Let's briefly go over the functionality of the other class methods:

1. set_mode:  This sets the mode wire to the desired mode ('idle', 'load', or 'run')
2. program_sequence:  This loads the experimental sequence to the fpga using a pipe.  The FPGA is set in 'load' mode during this process.
3. start_sequence:  This sets the mode to 'run'.  The FPGA then executes the experimental sequence
4. make_sequence_bytes:  This converts the sequence into a byte string that can be uploaded to the FPGA
5. write_channel_modes:  Sets the channels to either 'auto' or 'manual' mode
6. write_channel_manual_outputs:  Sets the output of all channels in 'manual' mode

We then define a child class for our specific TTL unit, defined in the file abcd.py, which provides device-specific information like the device_id and a list of channel objects. 

```python
class BoardABCD(YeSrDigitalBoard):
    okfpga_server_name = 'yeelmo_okfpga'
    okfpga_device_id = 'Ross_ttl'

    autostart = True

    channels = [
        DigitalChannel(loc=['A', 0], name='3D MOT AOM', mode='auto', manual_output=False, invert=True),
        DigitalChannel(loc=['A', 1], name='3D MOT Shutter', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 2], name='HR Abs. AOM', mode='auto', manual_output=False, invert=True),
        DigitalChannel(loc=['A', 3], name='HR Abs. Shutter', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 4], name='LR Abs. AOM', mode='auto', manual_output=False, invert=True),
        DigitalChannel(loc=['A', 5], name='LR H Abs. Shutter', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 6], name='LR V Abs. Shutter', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 7], name='2D MOT Shutter', mode='auto', manual_output=False, invert=True),
        DigitalChannel(loc=['A', 8], name='Zeeman Shutter', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 9], name='AH Enable', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 10], name='AH Bottom Enable', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 11], name='V Camera Trig.', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 12], name='H Camera Trig.', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 13], name='LR V Camera Trig.', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 14], name='TTLA14', mode='auto', manual_output=False, invert=False),
        DigitalChannel(loc=['A', 15], name='Gage Trig.', mode='auto', manual_output=False, invert=True),
        ]
    __device__ = BoardABCD
```

Here we've only included channel definitions for the first row for the sake of brevity.  The actual instance of this class contains channel objects for 64.

Finally, we discuss the SequencerServer class.  
  