import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QPlainTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, 
                               QStyledItemDelegate, QStackedWidget, QDialog, QDialogButtonBox, QFrame)
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QCoreApplication, Signal  
from openpyxl import Workbook
from as400_connector import AS400Connector
from system_monitor import SystemMonitorGUI
from user_manager import UserManager, UserManagerGUI
from job_manager import JobManager, JobManagerGUI
from utils import force_quit, setup_environment

class CustomItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(Qt.UserRole) == "category":
            option.font.setBold(True)
            option.font.setPointSize(option.font.pointSize() + 2)
            option.backgroundBrush = QColor("#E2E8F0")
        super().paint(painter, option, index)

class AS400ConnectorGUI(QMainWindow):
    connection_successful = Signal(object)  
    
    def __init__(self):
        super().__init__()
        setup_environment()
        self.as400_connector = AS400Connector()
        self.result = None
        self.connection_error = None
        self.user_managers = {}
        self.job_managers = {}
        self.current_connection = None
        self.initUI()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F4F8;
            }
            QLabel {
                color: #4A5568;
            }
            QLineEdit, QPlainTextEdit {
                background-color: #EDF2F7;
                color: #4A5568;
                border: 1px solid #CBD5E0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #63B3ED;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #4299E1;
            }
            QPushButton:disabled {
                background-color: #A0AEC0;
            }
            QTableWidget {
                background-color: #EDF2F7;
                color: #4A5568;
                gridline-color: #CBD5E0;
            }
            QTableWidget::item:selected {
                background-color: #BEE3F8;
            }
            QHeaderView::section {
                background-color: #E2E8F0;
                color: #4A5568;
                border: 1px solid #CBD5E0;
            }
            QMessageBox {
                background-color: #F0F4F8;
                color: #4A5568;
            }
            QMessageBox QLabel {
                color: #4A5568;
            }
            QMessageBox QPushButton {
                background-color: #63B3ED;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QComboBox {
                background-color: #EDF2F7;
                color: #4A5568;
                border: 1px solid #CBD5E0;
                border-radius: 5px;
                padding: 5px;
                min-height: 30px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #CBD5E0;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QComboBox QAbstractItemView {
                background-color: #EDF2F7;
                color: #4A5568;
                selection-background-color: #BEE3F8;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E0;
                background: #F0F4F8;
            }
            QTabBar::tab {
                background: #E2E8F0;
                border: 1px solid #CBD5E0;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #F0F4F8;
            }
        """)

    def initUI(self):
        self.setWindowTitle('DB400 多系統查詢工具')
        self.setGeometry(300, 300, 800, 600)

        # 創建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 創建堆疊小部件
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # 創建主界面和系統監控界面
        self.main_page = QWidget()
        self.system_monitor_page = SystemMonitorGUI(self)
        self.user_manager_page = QWidget()
        self.setup_user_manager_page()
        self.job_manager_page = QWidget()
        self.setup_job_manager_page()

        # 將兩個界面添加到堆疊小部件中
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.system_monitor_page)
        self.stacked_widget.addWidget(self.user_manager_page)
        self.stacked_widget.addWidget(self.job_manager_page)

        # 設置主界面佈局
        self.setup_main_page()

        self.statusBar().showMessage("準備就緒")
        self.statusBar().setStyleSheet("color: #4A5568; background-color: #E2E8F0;")

        # 快捷鍵
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self.connect_to_as400)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.show_disconnect_dialog)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.execute_query)

    def setup_main_page(self):
        layout = QVBoxLayout(self.main_page)

        # 創建標題和切換按鈕的水平佈局
        title_layout = QHBoxLayout()
        
        title_label = QLabel('DB400 多系統查詢工具')
        title_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4299E1; margin: 10px 0;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)  # 添加彈性空間
        
        self.switch_button = QPushButton('切換到系統監控')
        self.switch_button.clicked.connect(self.switch_interface)
        self.switch_button.setFixedSize(120, 30)  # 設置按鈕大小
        title_layout.addWidget(self.switch_button)
        
        self.user_manager_button = QPushButton('切換到用戶管理')
        self.user_manager_button.clicked.connect(self.switch_to_user_manager)
        self.user_manager_button.setFixedSize(120, 30)
        title_layout.addWidget(self.user_manager_button)
        
        self.job_manager_button = QPushButton('切換到作業管理')
        self.job_manager_button.clicked.connect(self.switch_to_job_manager)
        self.job_manager_button.setFixedSize(120, 30)
        title_layout.addWidget(self.job_manager_button)
        
        layout.addLayout(title_layout)

        def add_separator():
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("background-color: #CBD5E0;")
            layout.addWidget(line)

        add_separator()

        # 輸入欄（在同行）
        input_layout = QHBoxLayout()
        self.host_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        input_layout.addWidget(QLabel('系統名稱:'))
        input_layout.addWidget(self.host_input)
        input_layout.addWidget(QLabel('用戶名:'))
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(QLabel('密碼:'))
        input_layout.addWidget(self.password_input)

        # 將連接和中斷按鈕添加到輸入欄位後面
        self.connect_button = QPushButton('連接')
        self.connect_button.clicked.connect(self.connect_to_as400)
        input_layout.addWidget(self.connect_button)

        # 連接輸入欄位的textChanged信號到更新按鈕顏色的方法
        self.host_input.textChanged.connect(self.update_connect_button_color)
        self.user_input.textChanged.connect(self.update_connect_button_color)
        self.password_input.textChanged.connect(self.update_connect_button_color)

        self.disconnect_button = QPushButton('中斷')
        self.disconnect_button.clicked.connect(self.show_disconnect_dialog)
        self.disconnect_button.setEnabled(False)
        input_layout.addWidget(self.disconnect_button)

        layout.addLayout(input_layout)

        add_separator()

        # 添加系統選擇下拉選單
        self.system_combo = QComboBox()
        self.system_combo.addItem("選擇系統...")
        self.system_combo.currentIndexChanged.connect(self.switch_system)
        layout.addWidget(self.system_combo)

        self.query_input = QPlainTextEdit()
        self.query_input.setPlaceholderText("在此輸入SQL查詢...")
        self.query_input.setStyleSheet("font-family: 標楷體, KaiTi, SimKai; font-size: 12px;")
        layout.addWidget(self.query_input)

        self.execute_button = QPushButton('執行查詢')
        self.execute_button.clicked.connect(self.execute_query)
        self.execute_button.setEnabled(False)
        layout.addWidget(self.execute_button)

        add_separator()

        self.result_display = QTableWidget()
        layout.addWidget(self.result_display)

        self.export_button = QPushButton('匯出結果')
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)

    def update_connect_button_color(self):
        if self.host_input.text() and self.user_input.text() and self.password_input.text():
            self.connect_button.setStyleSheet("""
                QPushButton {
                    background-color: #63B3ED;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                }
                QPushButton:hover {
                    background-color: #4299E1;
                }
            """)
        else:
            self.connect_button.setStyleSheet("""
                QPushButton {
                    background-color: #A0AEC0;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                }
            """)

    def connect_to_as400(self):
        host = self.host_input.text()
        user = self.user_input.text()
        password = self.password_input.text()

        if not host or not user or not password:
            QMessageBox.warning(self, "輸入錯誤", "請填寫所有必要的連接信息")
            return

        connection, error = self.as400_connector.connect_to_as400(host, user, password)
        if connection:
            QMessageBox.information(self, "連接成功", f"已成功連接到IBM i系統: {host}")
            self.statusBar().showMessage(f"成功連接到 {host}")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.execute_button.setEnabled(True)
            
            if self.system_combo.findText(host) == -1:
                self.system_combo.addItem(host)
            self.system_combo.setCurrentText(host)
            
            # 清空輸入欄位
            self.host_input.clear()
            self.user_input.clear()
            self.password_input.clear()
            
            self.connection_error = None
            self.current_connection = host
            user_manager = UserManager(connection)
            self.user_managers[host] = UserManagerGUI(self, user_manager)
            self.job_managers[host] = JobManagerGUI(self, JobManager(connection))
            self.connection_successful.emit(connection)  # 發射信號
            self.update_current_connection()
            if host in self.job_managers:
                self.job_managers[host].enable_refresh()
        else:
            self.connection_error = error
            QMessageBox.critical(self, "連接失敗", f"無法連接到 {host}: {error}")
            self.statusBar().showMessage("連接失敗")
    def show_disconnect_dialog(self):
        if not self.as400_connector.connections:
            QMessageBox.warning(self, "無連接", "當前沒有活動的連接")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("選擇要中斷的連接")
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for host in self.as400_connector.connections.keys():
            combo.addItem(host)
        layout.addWidget(combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), dialog)
        shortcut.activated.connect(dialog.accept)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_host = combo.currentText()
            self.disconnect_from_as400(selected_host)

    def disconnect_from_as400(self, host):
        success, error = self.as400_connector.disconnect_from_as400(host)
        if success:
            index = self.system_combo.findText(host)
            if index != -1:
                self.system_combo.removeItem(index)
            QMessageBox.information(self, "斷開連接", f"已成功斷開與IBM i系統 {host} 的連接")
            
            if self.as400_connector.connections:
                self.system_combo.setCurrentText(self.as400_connector.current_connection)
                self.statusBar().showMessage(f"已切換到 {self.as400_connector.current_connection}")
            else:
                self.connect_button.setEnabled(True)
                self.disconnect_button.setEnabled(False)
                self.execute_button.setEnabled(False)
                self.export_button.setEnabled(False)
                self.statusBar().showMessage("已斷開所有連接")
                self.update_current_connection()
            
            if host in self.job_managers:
                self.job_managers[host].disable_refresh()
        else:
            QMessageBox.warning(self, "斷開連接警告", f"斷開連接时發生錯誤：{error}")
    def switch_system(self, index):
        if index == 0:  # "選擇系統..." 項
            return
        selected_system = self.system_combo.currentText()
        if self.as400_connector.switch_system(selected_system):
            self.statusBar().showMessage(f"已切換到系統: {selected_system}")
            self.current_connection = selected_system
            # 更新相關的管理器
            if selected_system in self.user_managers:
                self.user_manager = self.user_managers[selected_system]
            if selected_system in self.job_managers:
                self.job_manager = self.job_managers[selected_system]
        else:
            QMessageBox.warning(self, "切換失敗", f"無法切換到系統: {selected_system}")

    def execute_query(self):
        if not self.as400_connector.current_connection:
            QMessageBox.warning(self, "無連接", "請先連接到系統")
            return

        query = self.query_input.toPlainText()
        if not query:
            QMessageBox.warning(self, "查詢為空", "請輸入SQL查詢")
            return

        result, error = self.as400_connector.execute_query(query)
        if result:
            columns, data = result
            self.result = data
            
            self.result_display.setColumnCount(len(columns))
            self.result_display.setRowCount(len(self.result))
            self.result_display.setHorizontalHeaderLabels(columns)

            for row, rowData in enumerate(self.result):
                for col, value in enumerate(rowData):
                    self.result_display.setItem(row, col, QTableWidgetItem(str(value)))

            self.result_display.resizeColumnsToContents()
            self.statusBar().showMessage(f"查詢成功，返回 {len(self.result)} 行結果")
            self.export_button.setEnabled(True)
        else:
            QMessageBox.critical(self, "查詢失敗", f"執行查詢时發生錯誤: {error}")
            self.statusBar().showMessage("查詢執行失敗")

    def export_results(self):
        if not self.result:
            QMessageBox.warning(self, "無結果", "沒有可匯出的查詢結果")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "保存Excel文", "", "Excel Files (*.xlsx)")
        if not file_path:
            return

        try:
            wb = Workbook()
            ws = wb.active
            
            columns = [self.result_display.horizontalHeaderItem(i).text() for i in range(self.result_display.columnCount())]
            ws.append(columns)

            for row in self.result:
                ws.append(row)

            wb.save(file_path)
            QMessageBox.information(self, "匯出成功", f"查詢結果已成功匯出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "匯出失敗", f"匯出結果时發生錯誤: {str(e)}")
    
    def switch_interface(self):
        if self.stacked_widget.currentWidget() == self.main_page:
            self.stacked_widget.setCurrentWidget(self.system_monitor_page)
            self.switch_button.setText('切換到主界面')
        else:
            self.stacked_widget.setCurrentWidget(self.main_page)
            self.switch_button.setText('切換到系統監控')

    def switch_to_user_manager(self):
        if not self.user_managers or self.as400_connector.current_connection not in self.user_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")
            return
        self.stacked_widget.setCurrentWidget(self.user_manager_page)
        self.switch_button.setText('切換到系統監控')

    def switch_to_job_manager(self):
        if not self.job_managers or self.as400_connector.current_connection not in self.job_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")
            return
        self.stacked_widget.setCurrentWidget(self.job_manager_page)
        self.switch_button.setText('切換到系統監控')

    def closeEvent(self, event):
        for conn in self.as400_connector.connections.values():
            conn.close()
        event.accept()

    def setup_user_manager_page(self):
        layout = QVBoxLayout(self.user_manager_page)

        # 創建標題和切換按鈕的水平佈局
        title_layout = QHBoxLayout()
        
        title_label = QLabel('用戶管理')
        title_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4299E1; margin: 10px 0;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)  # 添加彈性空間
        
        return_button = QPushButton('切換到主界面')
        return_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.main_page))
        return_button.setFixedSize(120, 30)  # 設置按鈕大小
        title_layout.addWidget(return_button)
        
        layout.addLayout(title_layout)

        self.user_table = QTableWidget()
        layout.addWidget(self.user_table)
        
        button_layout = QHBoxLayout()
        create_user_button = QPushButton("新建用戶")
        create_user_button.clicked.connect(self.create_user_dialog)
        button_layout.addWidget(create_user_button)
        
        delete_user_button = QPushButton("刪除用戶")
        delete_user_button.clicked.connect(self.delete_user_dialog)
        button_layout.addWidget(delete_user_button)
        
        change_password_button = QPushButton("修改密碼")
        change_password_button.clicked.connect(self.change_password_dialog)
        button_layout.addWidget(change_password_button)
        
        disable_user_button = QPushButton("停用帳號")
        disable_user_button.clicked.connect(self.disable_user_dialog)
        button_layout.addWidget(disable_user_button)
        
        enable_user_button = QPushButton("啟用帳號")
        enable_user_button.clicked.connect(self.enable_user_dialog)
        button_layout.addWidget(enable_user_button)
        
        modify_authorities_button = QPushButton("修改權限")
        modify_authorities_button.clicked.connect(self.modify_user_authorities_dialog)
        button_layout.addWidget(modify_authorities_button)
        
        view_spool_files_button = QPushButton("查看 Spool Files")
        view_spool_files_button.clicked.connect(self.view_user_spool_files)
        button_layout.addWidget(view_spool_files_button)
        
        layout.addLayout(button_layout)
        
        refresh_button = QPushButton("刷新用戶列表")
        refresh_button.clicked.connect(self.refresh_user_list)
        layout.addWidget(refresh_button)

    def refresh_user_list(self):
        if not self.user_managers or self.as400_connector.current_connection not in self.user_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")
            return
        
        user_manager_gui = self.user_managers[self.as400_connector.current_connection]
        users = user_manager_gui.user_manager.list_users()  # 使用 UserManager 的 list_users 方法
        if users:
            columns, data = users
            self.user_table.setColumnCount(len(columns))
            self.user_table.setRowCount(len(data))
            self.user_table.setHorizontalHeaderLabels(columns)
            
            for row, user_data in enumerate(data):
                for col, value in enumerate(user_data):
                    self.user_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.user_table.resizeColumnsToContents()
            self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        else:
            QMessageBox.warning(self, "錯誤", "無法獲取用戶列表")
    def create_user_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].create_user_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def delete_user_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].delete_user_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def change_password_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].change_password_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def setup_job_manager_page(self):
        layout = QVBoxLayout(self.job_manager_page)

        # 創建標題和切換按鈕的水平佈局
        title_layout = QHBoxLayout()
        
        title_label = QLabel('作業管理')
        title_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #4299E1; margin: 10px 0;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)  # 添加彈性空間
        
        return_button = QPushButton('切換到主界面')
        return_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.main_page))
        return_button.setFixedSize(120, 30)  # 設置按鈕大小
        title_layout.addWidget(return_button)
        
        layout.addLayout(title_layout)

        self.job_table = QTableWidget()
        layout.addWidget(self.job_table)
        
        button_layout = QHBoxLayout()
        
        end_job_button = QPushButton("結束作業")
        end_job_button.clicked.connect(self.end_selected_job)
        button_layout.addWidget(end_job_button)
        
        hold_job_button = QPushButton("暫停作業")
        hold_job_button.clicked.connect(self.hold_selected_job)
        button_layout.addWidget(hold_job_button)
        
        release_job_button = QPushButton("釋放作業")
        release_job_button.clicked.connect(self.release_selected_job)
        button_layout.addWidget(release_job_button)
        
        layout.addLayout(button_layout)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_job_list)
        layout.addWidget(refresh_button)

    def refresh_job_list(self):
        if not self.job_managers or self.as400_connector.current_connection not in self.job_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")
            return
        
        job_manager_gui = self.job_managers[self.as400_connector.current_connection]
        jobs = job_manager_gui.job_manager.list_active_jobs()  # 使用 JobManager 的 list_active_jobs 方法
        if jobs:
            columns, data = jobs
            self.job_table.setColumnCount(len(columns))
            self.job_table.setRowCount(len(data))
            self.job_table.setHorizontalHeaderLabels(columns)
            
            for row, row_data in enumerate(data):
                for col, value in enumerate(row_data):
                    self.job_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.job_table.resizeColumnsToContents()
        else:
            QMessageBox.warning(self, "錯誤", "獲取活動作業列表失敗")

    def end_selected_job(self):
        if self.as400_connector.current_connection in self.job_managers:
            self.job_managers[self.as400_connector.current_connection].select_job_dialog("結束")
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")

    def hold_selected_job(self):
        if self.as400_connector.current_connection in self.job_managers:
            self.job_managers[self.as400_connector.current_connection].select_job_dialog("暫停")
        else:
            QMessageBox.warning(self, "錯", "未連接到系統或 JobManager 未初始化")

    def release_selected_job(self):
        if self.as400_connector.current_connection in self.job_managers:
            self.job_managers[self.as400_connector.current_connection].select_job_dialog("釋放")
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")

    def set_managers(self, user_manager, job_manager):
        self.user_managers[self.as400_connector.current_connection] = UserManagerGUI(self, user_manager)
        self.job_managers[self.as400_connector.current_connection] = JobManagerGUI(self, job_manager)

    def disable_user_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].disable_user_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def enable_user_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].enable_user_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def update_current_connection(self):
        if self.as400_connector.current_connection:
            self.system_combo.setCurrentText(self.as400_connector.current_connection)
            self.statusBar().showMessage(f"當前連接: {self.as400_connector.current_connection}")

    def modify_user_authorities_dialog(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].modify_authorities_dialog()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")

    def view_user_spool_files(self):
        if self.as400_connector.current_connection in self.user_managers:
            self.user_managers[self.as400_connector.current_connection].show_user_spool_files()
        else:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")