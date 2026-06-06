##################################
# PYTHON IOT RECEIVER WITH GUI
# Author: Kaden Downes
# Version: 0.1.0
##################################

import sys
import socket
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QGridLayout, QWidget, QLabel

# Thread class to receive packets from the sensor
class PacketReceiver(QThread):
    packet_received = pyqtSignal(bytes)

    # Initialize thread with specified host IP and port
    # Use IP 0.0.0.0 to listen for all clients
    # Port can be changed, but recommend leaving as 8080, as that's the port the sensor will expect.
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    # Run the packet receiver thread
    def run(self):
        # Socket setup
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(1)
        sock.settimeout(1.0)

        # Run until stopped
        while self.running:
            # See if a socket is trying to be opened
            try:
                client_sock, _ = sock.accept()
                client_sock.settimeout(1.0)

                # If opened, receive any transmitted data
                with client_sock:
                    while self.running:
                        try:
                            data = client_sock.recv(4096)
                            if not data:
                                break
                            # Emit received data from packet_received signal
                            self.packet_received.emit(data)
                        except socket.timeout:
                            continue
            except socket.timeout:
                pass

        # Close the listening port once we're done running
        sock.close()

    # Stop the packet receiver thread
    def stop(self):
        self.running = False
        self.wait()

class AlertsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alerts")

        ### GUI Elements ###
        self.buttonPressedLabel = QLabel("Button Pressed:")
        self.lowTempWarningLabel = QLabel("Low Temperature:")
        self.highTempWarningLabel = QLabel("High Temperature:")

        ### Layout Init ###
        layout = QGridLayout()
        layout.addWidget(self.buttonPressedLabel, 0, 0)
        layout.addWidget(self.lowTempWarningLabel, 1, 0)
        layout.addWidget(self.highTempWarningLabel, 2, 0)

        ### Widget Init ###
        self.setLayout(layout)

# Main GUI Window Setup
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("Zaetep's Sensor Data Receiver")

        ### GUI Elements ###

        # Initialize text area to be read only
        # TODO: Add separate areas for different kinds of received data
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        # Initialize start and stop buttons, make sure stop button is disabled
        self.start_button = QPushButton("Start Receiver")
        self.stop_button = QPushButton("Stop Receiver")
        self.stop_button.setEnabled(False)
        self.alerts_button = QPushButton("Alerts")
        # self.liveview_button = QPushButton("Live Data")

        ### Layout Init ###

        # Initialize layout
        layout = QGridLayout()
        layout.addWidget(self.start_button, 0, 0, 1, 1)
        layout.addWidget(self.stop_button, 1, 0, 1, 1)
        layout.addWidget(self.alerts_button, 0, 1, 2, 1)

        ### Widget Init ###

        # Initialize Widget container
        container = QWidget()
        # Use our layout for the container
        container.setLayout(layout)
        # Our container is the only Widget, so make it the main
        self.setCentralWidget(container)

        # Initialize vars
        self.worker = None
        self.alerts_window = None

        ### Connect Functionality ###

        # Connect start button to start receiver
        self.start_button.clicked.connect(self.start_receiver)
        # Connect stop button to stop receiver
        self.stop_button.clicked.connect(self.stop_receiver)
        # Connect alerts button to open alerts window
        self.alerts_button.clicked.connect(self.show_alerts_window)

    # Start receiver task
    def start_receiver(self):
        # Worker initialized with port 8080, listening for all
        self.worker = PacketReceiver("0.0.0.0", 8080)
        # Connect packet_received signal to display_packet function
        self.worker.packet_received.connect(self.display_packet)
        # Start the worker
        self.worker.start()

        # Make sure we can't start twice and that we can stop
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    # Stop receiver task
    def stop_receiver(self):
        # If worker exists, stop it and return worker value to None
        if self.worker:
            self.worker.stop()
            self.worker = None

        # Re-enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    # Show alerts window
    def show_alerts_window(self):
        if self.alerts_window is None:
            self.alerts_window = AlertsWindow()
        self.alerts_window.show()
        self.alerts_window.raise_()
        self.alerts_window.activateWindow()

    # Display the received data in the text box
    # TODO: Parse an HTTP packet and add logic to display different types of alerts
    def display_packet(self, data):
        self.text_area.append(f"Received: {data.decode(errors='replace')}")


# Start Application
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
