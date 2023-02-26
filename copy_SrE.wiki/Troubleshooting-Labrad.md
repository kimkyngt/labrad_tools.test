# Starting up labrad

This tutorial describes how to restart labrad assuming that everything is off.  For example, if YeElmo (labrad host) shut down for some reason one would pretty much need to restart everything.  First, if there are any labrad servers or clients running on any other machine, close them.  The YeElmo labrad manager and labrad node are currently configured to automatically start up when YeElmo is first turned on.  To check to make sure that things booted up properly, one can do the following:

Open an ipython terminal on any computer configured to run labrad (currently: YeElmo, YeBigBird, YeCookieMonster,  YeOscarTheGrouch, and YeKermit) and enter the following:  

```python
In [1]: import labrad
In [2]: cxn = labrad.connect()
```

If you are able to connect to labrad, this means that the labrad manager is running on YeElmo.  Several labrad servers are configured to start automatically on YeElmo when the labrad node is initiated.  To see which servers are started automatically, enter the following

```python
In [3]: cxn.node_yeelmo.autostart_list()
Out[3]: 
['current_controller',
 'okfpga',
 'picoscope',
 'pmt',
 'rf',
 'sequencer',
 'serial']
```

Typically, all of the servers listed above except the sequencer start without issue.  Sometimes the sequencer won't initiallize its devices properly and requires an additional restart.  This happens when the sequencer server attempts to start and the okfpga server hasn't finished initializing the fpga devices.  Enter the following:

```python
In [4]: cxn.sequencer.list_devices()
Out[4]: '{"active": ["abcd", "e"], "configured": ["abcd", "e", "f", "g"]}'
```

If the "abcd" and "e" devices aren't listed as "active", the sequencer needs to be restarted as follows:

```python
In [5]: cxn.node_yeelmo.restart('sequencer')
```

Check list_devices() again to make sure that the sequencer has initialized properly.  Once this is complete, it is time to start the conductor server on YeElmo.  I don't include this device in autostart because it is useful to run it separately so we can monitor any output messages.  I typically ssh to YeElmo from YeBigBird and leave the conductor terminal running on the right side of the screen so we can keep an eye on the output.  To ssh to YeElmo, open a terminal on YeBigBird and type "elmo" and hit enter.  Enter the usual password then do the following:

```bash
>> cd SrE/labrad_tools/conductor
>> python conductor.py
```

The conductor should now be running.  Open up another terminal tab and ssh to YeElmo again and enter the following:

```bash
>> cd SrE/labrad_tools/systemd
>> ./labrad-node-journal
```

This will open a monitor program that will output any messages from any server running on the YeElmo labrad node.  Now labrad should be up and running.  We also want to start the plotter server to plot data from our experiment.  Currently this server is run from YeCookieMonster since that computer is running an apache server to post the plots online and the conductor is configured to look for plotter data on YeCookieMonster.  On YeCookieMonster:

```bash
>> labrad
>> cd plotter
>> python plotter.py
```

Now all of the servers are running.  One may wish to open some clients as well.  We often use the following:

1. labrad_tools/sequencer/clients/sequencer_control.py
2. labrad_tools/pmt/clients/pmt_client.py
3. labrad_tools/conductor/clients/clock_fiber_aom_control.py  #type hr_demod_frequency into the upper-right box
4. labrad_tools/current_controller/clients/blue_slave_control.py

# Rebooting labrad

Sometimes someone crashes one of the servers and we just can't get things running again.  It may be necessary to restart everything to get things working again.  First close any open labrad server or client running on YeBigBird or YeCookieMonster (or any other workstation) and close the conductor on YeElmo.  At this point, ssh onto YeElmo and restart the labrad manager and labrad node as follows:

```bash
>> sudo systemctl restart labrad-manager.service
>> sudo systemctl restart labrad-node.service
```

Then follow the instructions in the first section for starting up labrad.