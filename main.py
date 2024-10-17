import sys
<<<<<<< Updated upstream
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
=======
# from PySide6.QtCore import QTimer  # 移除未使用的 QTimer 導入
>>>>>>> Stashed changes
from gui import AS400ConnectorGUI
from user_manager import UserManager
from job_manager import JobManager
from as400_connector import AS400Connector
<<<<<<< Updated upstream
=======
from utils import setup_environment
import logging  # 添加此行以導入 logging 模組
from PySide6.QtWidgets import QApplication  # 確保 PySide6 已正確安裝
>>>>>>> Stashed changes

def create_application():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 風格以獲得更現代的外觀
    return app

def setup_main_gui():
    main_gui = AS400ConnectorGUI()
    return main_gui

<<<<<<< Updated upstream
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
=======
# 確保在使用之前定義 initialize_managers 函數
def initialize_managers(main_gui, connection):
    # ... 函數實現 ...
    pass  # 替換為實際代碼

def get_active_connection(main_gui):
    return main_gui.as400_connector.connections.get(main_gui.as400_connector.current_connection)
>>>>>>> Stashed changes

def main():
    app = create_application()
    main_gui = setup_main_gui()
    
    # 使用 QTimer 來延遲執行初始化和顯示 GUI
    QTimer.singleShot(0, lambda: initialize_managers(main_gui))
    QTimer.singleShot(0, main_gui.show)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
