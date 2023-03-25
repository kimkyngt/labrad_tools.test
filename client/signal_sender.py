from twisted.internet.defer import inlineCallbacks
from PyQt5 import QtWidgets

class ReceiverWidget(QtWidgets.QWidget):

    ID = 123456
    # this is an ID for the client to register to the server

    def __init__(self, parent=None):
        super(ReceiverWidget, self).__init__(parent)
        self.setupLayout()
        self.connect()

    def setupLayout(self):
        # setup the layout and make all the widgets
        self.setWindowTitle('Sender Widget')
        # create a horizontal layout
        layout = QtWidgets.QHBoxLayout()
        # create a button for server to ask server to send a signal
        self.sendbutton = QtWidgets.QPushButton("Send signal")
        self.sendbutton.setGeometry(600, 150, 100, 30)
        self.sendbutton.clicked.connect(self.clickme)

        layout.addWidget(self.sendbutton)
        self.setLayout(layout)
        
    def clickme(self):
        self.server.emit_signal()
        print("press")

    @inlineCallbacks
    def connect(self):
        import labrad
        cxn = labrad.connect()
        self.server = yield cxn.yesr_sr1_test_emitterserver


if __name__ == '__main__':
    # join Qt and twisted event loops
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = ReceiverWidget()
    widget.show()
    app.exec()
