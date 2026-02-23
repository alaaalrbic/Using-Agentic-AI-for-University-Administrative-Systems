import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from UI.university_gui import MainWindow
def main() -> None:
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 9)
    app.setFont(font) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()