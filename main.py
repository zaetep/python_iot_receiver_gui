##################################
# PYTHON IOT RECEIVER WITH GUI
# Author: Kaden Downes
# Version: 0.1.0
##################################

import sys
import socket
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget

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

                # If opened, receive the data and close the socket once received
                with client_sock:
                    while self.running:
                        try:
                            data = client_sock.recv(4096)
                            if not data:
                                break
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

# Main GUI Window Setup
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("Sensor Data Receiver")

        # Initialize text area to be read only
        # TODO: Add separate areas for different kinds of received data
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        # Initialize start and stop buttons, make sure stop button is disabled
        self.start_button = QPushButton("Start Receiver")
        self.stop_button = QPushButton("Stop Receiver")
        self.stop_button.setEnabled(False)

        # Initialize layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        # Initialize Widget container
        container = QWidget()
        # Use our layout for the container
        container.setLayout(layout)
        # Our container is the only Widget, so make it the main
        self.setCentralWidget(container)

        # Initialize worker to be None
        self.worker = None

        # Connect start button to start receiver
        self.start_button.clicked.connect(self.start_receiver)
        # Connect stop button to stop receiver
        self.stop_button.clicked.connect(self.stop_receiver)

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

    # Display the received data in the text box
    # TODO: Parse an HTTP packet and add logic to display different types of alerts
    def display_packet(self, data):
        self.text_area.append(f"Received: {data.decode(errors='replace')}")


# Start Application
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
