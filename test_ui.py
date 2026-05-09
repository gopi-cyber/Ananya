import sys
from PyQt6.QtWidgets import QApplication
from UI.dashboard import DashboardUI

def main():
    app = QApplication(sys.argv)
    try:
        window = DashboardUI()
        window.show()
        print("Dashboard initialized and showing")
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
