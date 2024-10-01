import jaydebeapi

class JobManager:
    def __init__(self, connection):
        self.connection = connection

    def list_active_jobs(self):
        """列出所有活動作業"""
        query = """
        SELECT JOB_NAME, AUTHORIZATION_NAME, JOB_TYPE, FUNCTION, SUBSYSTEM
        FROM TABLE(QSYS2.ACTIVE_JOB_INFO()) 
        ORDER BY SUBSYSTEM, JOB_NAME
        """
        return self._execute_query(query)

    def end_job(self, job_name):
        """結束指定作業"""
        query = f"CALL QSYS.ENDJOB('{job_name}', 'CNTRLD', '')"
        self._execute_query(query)

    def hold_job(self, job_name):
        """暫停指定作業"""
        query = f"CALL QSYS.HLDJOB('{job_name}')"
        self._execute_query(query)

    def release_job(self, job_name):
        """釋放指定作業"""
        query = f"CALL QSYS.RLSJOB('{job_name}')"
        self._execute_query(query)

    def _execute_query(self, query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    columns = [desc[0] for desc in cursor.description]
                    result = cursor.fetchall()
                    return columns, result
                else:
                    return None
        except Exception as e:
            print(f"執行查詢時發生錯誤: {str(e)}")
            return None

class JobManagerGUI:
    def __init__(self, parent, job_manager):
        self.parent = parent
        self.job_manager = job_manager

    def list_active_jobs(self):
        """列出所有活動作業"""
        result = self.job_manager.list_active_jobs()
        if result:
            columns, data = result
            self.job_table.setColumnCount(len(columns))
            self.job_table.setRowCount(len(data))
            self.job_table.setHorizontalHeaderLabels(columns)
            for row, job_data in enumerate(data):
                for col, value in enumerate(job_data):
                    self.job_table.setItem(row, col, QTableWidgetItem(str(value)))
            self.job_table.resizeColumnsToContents()
        else:
            QMessageBox.warning(self, "錯誤", "獲取活動作業列表失敗")

    def end_selected_job(self):
        self.job_manager.end_job(self.selected_job_name)

    def hold_selected_job(self):
        self.job_manager.hold_job(self.selected_job_name)

    def release_selected_job(self):
        self.job_manager.release_job(self.selected_job_name)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt

class JobManagerGUI(QWidget):
    def __init__(self, parent, job_manager):
        super().__init__(parent)
        self.parent = parent
        self.job_manager = job_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 創建按鈕
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新作業列表')
        self.end_button = QPushButton('結束作業')
        self.hold_button = QPushButton('暫停作業')
        self.release_button = QPushButton('釋放作業')

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.end_button)
        button_layout.addWidget(self.hold_button)
        button_layout.addWidget(self.release_button)

        layout.addLayout(button_layout)

        # 創建表格
        self.job_table = QTableWidget()
        layout.addWidget(self.job_table)

        # 連接按鈕信號
        self.refresh_button.clicked.connect(self.refresh_job_list)
        self.end_button.clicked.connect(self.end_selected_job)
        self.hold_button.clicked.connect(self.hold_selected_job)
        self.release_button.clicked.connect(self.release_selected_job)

        # 初始化作業列表
        self.refresh_job_list()

    def refresh_job_list(self):
        result = self.job_manager.list_active_jobs()
        if result:
            columns, data = result
            self.job_table.setColumnCount(len(columns))
            self.job_table.setRowCount(len(data))
            self.job_table.setHorizontalHeaderLabels(columns)

            for row, job_data in enumerate(data):
                for col, value in enumerate(job_data):
                    self.job_table.setItem(row, col, QTableWidgetItem(str(value)))

            self.job_table.resizeColumnsToContents()
        else:
            QMessageBox.warning(self, "錯誤", "無法獲取作業列表")

    def get_selected_job(self):
        selected_items = self.job_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "請先選擇一個作業")
            return None
        return selected_items[0].text()  # 假設第一列是作業名稱

    def end_selected_job(self):
        job_name = self.get_selected_job()
        if job_name:
            confirm = QMessageBox.question(self, "確認", f"確定要結束作業 {job_name} 嗎？",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.job_manager.end_job(job_name)
                self.refresh_job_list()

    def hold_selected_job(self):
        job_name = self.get_selected_job()
        if job_name:
            self.job_manager.hold_job(job_name)
            self.refresh_job_list()

    def release_selected_job(self):
        job_name = self.get_selected_job()
        if job_name:
            self.job_manager.release_job(job_name)
            self.refresh_job_list()
