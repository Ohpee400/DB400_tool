import sys
from PySide6.QtWidgets import QApplication
from gui import AS400ConnectorGUI
from user_manager import UserManager
from job_manager import JobManager
from as400_connector import connect_to_as400

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 風格以獲得更現代的外觀
    
    # 創建主 GUI 實例
    main_gui = AS400ConnectorGUI()
    
    # 當連接成功時，創建 UserManager 和 JobManager 實例
    def on_connection_success(connection):
        user_manager = UserManager(connection)
        job_manager = JobManager(connection)
        
        # 將 UserManager 和 JobManager 實例傳遞給主 GUI
        main_gui.set_managers(user_manager, job_manager)
    
    # 將連接成功的信號連接到我們的處理函數
    main_gui.connection_successful.connect(on_connection_success)
    
    main_gui.show()
    sys.exit(app.exec())