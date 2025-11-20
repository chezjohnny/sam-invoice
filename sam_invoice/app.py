import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Facturation - Marchand de vin")
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        button = QPushButton("Cliquez-moi")
        layout.addWidget(button)
        self.setCentralWidget(central_widget)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Facturation")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
