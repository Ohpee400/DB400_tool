import jaydebeapi
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QDialog, QListWidget, QDialogButtonBox
from PySide6.QtCore import Qt

class JobManager:
    def __init__(self, connection):
        self.connection = connection

    def list_active_jobs(self):
        """列出所有活動作業"""
        query = """
        SELECT JOB_NAME, AUTHORIZATION_NAME AS USER, JOB_TYPE, FUNCTION, SUBSYSTEM
        FROM TABLE(QSYS2.ACTIVE_JOB_INFO()) 
        ORDER BY SUBSYSTEM, JOB_NAME
        """
        return self._execute_query(query)

    def end_job(self, job_name):
        """結束指定作業"""
        cmd = f"ENDJOB JOB({job_name}) OPTION(*CNTRLD)"
        self._execute_command(cmd)

    def hold_job(self, job_name):
        """暫停指定作業"""
        cmd = f"HLDJOB JOB({job_name})"
        self._execute_command(cmd)

    def release_job(self, job_name):
        """釋放指定作業"""
        cmd = f"RLSJOB JOB({job_name})"
        self._execute_command(cmd)

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

    def _execute_command(self, cmd):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("CALL QSYS2.QCMDEXC(?)", (cmd,))
        except Exception as e:
            print(f"執行命令時發生錯誤: {str(e)}")
            raise

class JobManagerGUI(QWidget):
    def __init__(self, parent, job_manager):
        super().__init__(parent)
        self.parent = parent
        self.job_manager = job_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 創建篩選控件
        filter_layout = QHBoxLayout()
        self.subsystem_filter = QLineEdit()
        self.subsystem_filter.setPlaceholderText("按子系統篩選")
        self.user_filter = QLineEdit()
        self.user_filter.setPlaceholderText("按用戶名篩選")
        filter_layout.addWidget(self.subsystem_filter)
        filter_layout.addWidget(self.user_filter)
        layout.addLayout(filter_layout)

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
        self.end_button.clicked.connect(lambda: self.select_job_dialog("結束"))
        self.hold_button.clicked.connect(lambda: self.select_job_dialog("暫停"))
        self.release_button.clicked.connect(lambda: self.select_job_dialog("釋放"))

        # 連接篩選信號
        self.subsystem_filter.textChanged.connect(self.apply_filters)
        self.user_filter.textChanged.connect(self.apply_filters)

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
            self.apply_filters()
        else:
            QMessageBox.warning(self, "錯誤", "無法獲取作業列表")

    def apply_filters(self):
        subsystem_filter = self.subsystem_filter.text().lower()
        user_filter = self.user_filter.text().lower()

        for row in range(self.job_table.rowCount()):
            subsystem = self.job_table.item(row, 1).text().lower()  # 假設子系統在第2列
            user = self.job_table.item(row, 2).text().lower()  # 假設用戶名在第3列
            if subsystem_filter in subsystem and user_filter in user:
                self.job_table.setRowHidden(row, False)
            else:
                self.job_table.setRowHidden(row, True)

    def select_job_dialog(self, action):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"選擇要{action}的作業")
        layout = QVBoxLayout(dialog)

        job_list = QListWidget()
        for row in range(self.job_table.rowCount()):
            if not self.job_table.isRowHidden(row):
                job_name = self.job_table.item(row, 0).text()
                job_list.addItem(job_name)
        layout.addWidget(job_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            selected_items = job_list.selectedItems()
            if selected_items:
                job_name = selected_items[0].text()
                if action == "結束":
                    self.end_selected_job(job_name)
                elif action == "暫停":
                    self.hold_selected_job(job_name)
                elif action == "釋放":
                    self.release_selected_job(job_name)
            else:
                QMessageBox.warning(self, "警告", "請選擇一個作業")

    def end_selected_job(self, job_name):
        confirm = QMessageBox.question(self, "確認", f"確定要結束作業 {job_name} 嗎？",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                self.job_manager.end_job(job_name)
                QMessageBox.information(self, "成功", f"作業 {job_name} 已成功結束")
                self.refresh_job_list()
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"結束作業時發生錯誤: {str(e)}")

    def hold_selected_job(self, job_name):
        try:
            self.job_manager.hold_job(job_name)
            QMessageBox.information(self, "成功", f"作業 {job_name} 已成功暫停")
            self.refresh_job_list()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"暫停作業時發生錯誤: {str(e)}")

    def release_selected_job(self, job_name):
        try:
            self.job_manager.release_job(job_name)
            QMessageBox.information(self, "成功", f"作業 {job_name} 已成功釋放")
            self.refresh_job_list()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"釋放作業時發生錯誤: {str(e)}")