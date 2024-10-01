import sys
from PySide6.QtWidgets import QApplication
from gui import AS400ConnectorGUI
from user_manager import UserManager
from job_manager import JobManager
from as400_connector import connect_to_as400

def create_application():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 风格以獲得更現代的外觀
    return app

def setup_main_gui():
    main_gui = AS400ConnectorGUI()

    def on_connection_success(connection):
        user_manager = UserManager(connection)
        job_manager = JobManager(connection)
        main_gui.set_managers(user_manager, job_manager)

    main_gui.connection_successful.connect(on_connection_success)
    return main_gui

def main():
    app = create_application()
    main_gui = setup_main_gui()
    main_gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()