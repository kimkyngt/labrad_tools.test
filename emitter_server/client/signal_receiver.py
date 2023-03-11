from twisted.internet.defer import inlineCallbacks
from PyQt5 import QtWidgets

class ReceiverWidget(QtWidgets.QWidget):

    ID = 123456
    # this is an ID for the client to register to the server

    def __init__(self, reactor, parent=None):
        super(ReceiverWidget, self).__init__(parent)
        self.reactor = reactor
        self.setupLayout()
        self.connect()

    def setupLayout(self):
        # setup the layout and make all the widgets
        self.setWindowTitle('Receiver Widget')
        # create a horizontal layout
        layout = QtWidgets.QHBoxLayout()
        # create the text widget
        self.textedit = QtWidgets.QTextEdit()
        self.textedit.setReadOnly(True)
        layout.addWidget(self.textedit)
        self.setLayout(layout)

    @inlineCallbacks
    def connect(self):
        # make an asynchronous connection to LabRAD
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync(name='Signal Widget')
        self.server = cxn.emitter_server
        # connect to emitter server
        yield self.server.signal__emitted_signal(self.ID)
        # connect to signal from server (note the method is named from parsed
        # text of the in the server emitter name)
        yield self.server.addListener(listener=self.displaySignal,
                                       source=None, ID=self.ID)
        # This registers the client as a listener to the server and assigns a
        # slot (function) from the client to the signal emitted from the server
        # In this case self.displaySignal

    def displaySignal(self, cntx, signal):
        self.textedit.append(signal)

    def closeEvent(self, event):
        # stop the reactor when closing the widget
        self.reactor.stop()

if __name__ == '__main__':
    # join Qt and twisted event loops
    import sys
    app = QtWidgets.QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    widget = ReceiverWidget(reactor)
    widget.show()
    reactor.run()
