from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QLineEdit, QComboBox, QTabWidget, QTableWidgetItem, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from as400_connector import execute_query

class SystemMonitorGUI(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_gui = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 創建標題和切換按鈕的水平佈局
        title_layout = QHBoxLayout()
        
        title_label = QLabel('系統監控')
        title_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4299E1; margin: 10px 0;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)  # 添加彈性空間
        
        switch_to_main_button = QPushButton('切換到主界面')
        switch_to_main_button.clicked.connect(self.parent_gui.switch_interface)
        switch_to_main_button.setFixedSize(120, 30)  # 設置按鈕大小
        title_layout.addWidget(switch_to_main_button)
        
        layout.addLayout(title_layout)

        # 創建選項卡窗口部件
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 添加 QSYSOPR 消息隊列監控選項卡
        self.add_qsysopr_tab(self.tab_widget)

        # 添加歷史日誌監控選項卡
        self.add_history_log_tab(self.tab_widget)

        # 添加作業日誌監控選項卡
        self.add_job_log_tab(self.tab_widget)

    def add_qsysopr_tab(self, tab_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        query_button = QPushButton('查詢 QSYSOPR 消息')
        query_button.clicked.connect(self.query_qsysopr)
        layout.addWidget(query_button)

        self.qsysopr_result = QTableWidget()
        layout.addWidget(self.qsysopr_result)

        tab_widget.addTab(tab, 'QSYSOPR 消息')

    def query_qsysopr(self):
        query = """
        SELECT MESSAGE_TEXT, MESSAGE_ID, SEVERITY, FROM_JOB, MESSAGE_TIMESTAMP 
        FROM QSYS2.MESSAGE_QUEUE_INFO
        WHERE MESSAGE_QUEUE_NAME = 'QSYSOPR' AND SEVERITY > 10
        ORDER BY MESSAGE_TIMESTAMP DESC
        FETCH FIRST 100 ROWS ONLY
        """
        self.execute_query(query, self.qsysopr_result)

    def add_history_log_tab(self, tab_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        query_button = QPushButton('查詢歷史日誌')
        query_button.clicked.connect(self.query_history_log)
        layout.addWidget(query_button)

        self.history_log_result = QTableWidget()
        layout.addWidget(self.history_log_result)

        tab_widget.addTab(tab, '歷史日誌')

    def query_history_log(self):
        query = """
        SELECT MESSAGE_TEXT, MESSAGE_ID, SEVERITY, FROM_JOB, MESSAGE_TIMESTAMP 
        FROM TABLE(QSYS2.HISTORY_LOG_INFO(
            START_TIME => CURRENT TIMESTAMP - 24 HOURS)) X
        WHERE SEVERITY >= '30'
        ORDER BY MESSAGE_TIMESTAMP DESC
        """
        self.execute_query(query, self.history_log_result)

    def add_job_log_tab(self, tab_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        job_input = QLineEdit()
        job_input.setPlaceholderText('輸入作業名稱 (例如: 123456/USERNAME/JOBNAME)')
        job_input.textChanged.connect(lambda text: job_input.setText(text.upper()))  # 將輸入轉換為大寫
        layout.addWidget(job_input)

        query_button = QPushButton('查詢作業日誌')
        query_button.clicked.connect(lambda: self.query_job_log(job_input.text()))
        layout.addWidget(query_button)

        self.job_log_result = QTableWidget()
        layout.addWidget(self.job_log_result)

        tab_widget.addTab(tab, '作業日誌')

    def query_job_log(self, job_name):
        query = f"""
        SELECT MESSAGE_TEXT, MESSAGE_ID, MESSAGE_TYPE, MESSAGE_TIMESTAMP
        FROM TABLE(QSYS2.JOBLOG_INFO('{job_name}')) AS X
        ORDER BY MESSAGE_TIMESTAMP DESC
        FETCH FIRST 100 ROWS ONLY
        """
        self.execute_query(query, self.job_log_result)

    def execute_query(self, query, result_widget):
        if not self.parent_gui.as400_connector.current_connection:
            QMessageBox.warning(self, "無連接", "請先選擇一個連接的系統")
            return

        result, error = self.parent_gui.as400_connector.execute_query(query)
        if result:
            columns, data = result
            
            result_widget.setColumnCount(len(columns))
            result_widget.setRowCount(len(data))
            result_widget.setHorizontalHeaderLabels(columns)

            for row, rowData in enumerate(data):
                for col, value in enumerate(rowData):
                    result_widget.setItem(row, col, QTableWidgetItem(str(value)))

            result_widget.resizeColumnsToContents()
        else:
            QMessageBox.critical(self, "查詢失敗", f"執行查詢時發生錯誤: {error}")