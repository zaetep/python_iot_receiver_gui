import sys
import socket
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget


class PacketReceiver(QThread):
    packet_received = pyqtSignal(bytes)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(1)
        sock.settimeout(1.0)

        while self.running:
            try:
                client_sock, _ = sock.accept()
                client_sock.settimeout(1.0)

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

        sock.close()

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sensor Data Receiver")

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        self.start_button = QPushButton("Start Receiver")
        self.stop_button = QPushButton("Stop Receiver")
        self.stop_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker = None

        self.start_button.clicked.connect(self.start_receiver)
        self.stop_button.clicked.connect(self.stop_receiver)

    def start_receiver(self):
        self.worker = PacketReceiver("0.0.0.0", 8080)
        self.worker.packet_received.connect(self.display_packet)
        self.worker.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_receiver(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def display_packet(self, data):
        self.text_area.append(f"Received: {data.decode(errors='replace')}")


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
