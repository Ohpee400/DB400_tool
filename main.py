import sys
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gui import AS400ConnectorGUI
from user_manager import UserManager
from job_manager import JobManager
from as400_connector import AS400Connector

def create_application():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 風格以獲得更現代的外觀
    return app

def setup_main_gui():
    main_gui = AS400ConnectorGUI()
    return main_gui

def initialize_managers(main_gui):
    # 同步初始化 AS400Connector
    connector = AS400Connector()
    
    # 使用 main_gui 中的連接信息
    connection = main_gui.as400_connector.connections.get(main_gui.as400_connector.current_connection)
    
    if not connection:
        print("錯誤: 沒有活動的連接")
        return
    
    # 初始化 UserManager 和 JobManager
    user_manager = UserManager(connection)
    job_manager = JobManager(connection)
    
    # 設置 managers
    main_gui.set_managers(user_manager, job_manager)

def main():
    app = create_application()
    main_gui = setup_main_gui()
    
    # 使用 QTimer 來延遲執行初始化和顯示 GUI
    QTimer.singleShot(0, lambda: initialize_managers(main_gui))
    QTimer.singleShot(0, main_gui.show)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()