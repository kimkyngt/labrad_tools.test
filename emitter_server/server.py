"""
### BEGIN NODE INFO
[info]
name = Emitter Server
version = 1.0
description = 
instancename = %LABRADNODE%_EmitterServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
import labrad

class EmitterServer(LabradServer):
    """
    Basic Emitter Server
    """
    name = "%LABRADNODE%_EmitterServer"
    def __init__(self):
        super().__init__()
        
    onNotification = Signal(1234, 'signal: test', 's')

    @setting(10, message='s')
    def notify_clients(self, c, message):
        self.onNotification(message)  # send the message to all listening clients

Server = EmitterServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
