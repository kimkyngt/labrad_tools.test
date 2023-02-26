# Setting up the server on YeCountVonCount
This is relatively straightforward

1. Install the Apache server
2. Start the server
3. Move the new_plotter html code so the server can see it
4. Add apache to /etc/init.d/ so it will start when the computer is booted up

```bash
> sudo apt-get install apache2

> sudo systemctl start apache2

> sudo cp ~/GitRepo/SrE/labrad_tools/plotter/html/new_plotter.html /var/www/html/new_plotter

> sudo update-rc.d apache2 defaults
```
Now the server is running.  Any computer on the network can now see the plotter page by going to yecookiemonster.colorado.edu/new_plotter with a web browser.

# The plotter server

```python

```
