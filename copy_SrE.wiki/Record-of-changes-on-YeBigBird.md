# Change Log

The purpose of this log is to track changes that we make to the YeBigBird computer in order to fix issues with running labrad or to make our user experience better.  This will allow us to keep track of how the computer is set up so we can propagate these changes to other machines if desired or know which packages to uninstall if the computer mysteriously starts behaving badly.  

### 8/30/18  Added terminal feature to Dolphin

I received some feedback about how it is difficult to run python code that one finds via the file browser.  I've added an interactive terminal feature to Dolphin.  

**Dolphin**

```bash
>> sudo apt-get install konsole
```

Now when the file browser is open, simply hit "F4" to open an imbedded terminal at the bottom of the page.  "Alt+F4" will open a terminal in a new window.

### 8/30/18 Added plugins for gedit

```bash
>> sudo apt-get install gedit-plugins
```

Enabled the following plugins:  Code Comment, Embedded Terminal, Embedded Python console, Smart Spaces, Modelines, Word Completion, git

To Open up a terminal at the bottom of the window, hit "ctrl+F9"