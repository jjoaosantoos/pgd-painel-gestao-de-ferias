import sys
from PyQt6.QtWidgets import QApplication
from ui.tela_login import TelaLogin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = TelaLogin()
    login.show()
    sys.exit(app.exec())
    