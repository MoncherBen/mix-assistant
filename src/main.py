"""
####### main.py #######

### Auth: MoncherBen, Oct. 2026
"""


import sys

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow



def main():
    """ Typically. """
    app = QApplication(sys.argv)
    app.setApplicationName("Mix Assistant")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
