import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QPlainTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, 
                               QStyledItemDelegate, QStackedWidget, QDialog, QDialogButtonBox, QFrame)
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QCoreApplication, Signal  
from openpyxl import Workbook
from as400_connector import connect_to_as400, disconnect_from_as400, execute_query
from system_monitor import SystemMonitorGUI
from user_manager import UserManager
from job_manager import JobManager

# 確保程序完全退出
def force_quit():
    QCoreApplication.quit()
    sys.exit(0)

jt400_path = "/Users/clark/Desktop/DDSC/Clark文件/13-JavaCode/jt400.jar"
if not os.path.exists(jt400_path):
    print(f"錯誤：jt400.jar 文件未找到：{jt400_path}")
    sys.exit(1)

java_home = "/Library/Java/JavaVirtualMachines/jdk-22.jdk/Contents/Home"
os.environ["JAVA_HOME"] = java_home
os.environ["PATH"] = f"{java_home}/bin:{os.environ.get('PATH', '')}"
os.environ["CLASSPATH"] = f"{jt400_path}:{os.environ.get('CLASSPATH', '')}"

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
        self.connections = {}  # 存儲多個連接
        self.current_connection = None
        self.result = None
        self.connection_error = None
        self.user_managers = {}
        self.job_managers = {}
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

        # 輸入欄位（在同一行）
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
        self.query_input.setStyleSheet("font-family: Consolas, Monaco, monospace; font-size: 12px;")
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

        connection, error = connect_to_as400(host, user, password)
        if connection:
            self.connections[host] = connection
            self.current_connection = host
            
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
            self.user_managers[host] = UserManager(connection)
            self.job_managers[host] = JobManager(connection)
            self.connection_successful.emit(connection)  # 發射信號
        else:
            self.connection_error = error
            QMessageBox.critical(self, "連接失敗", f"無法連接到 {host}: {error}")
            self.statusBar().showMessage("連接失敗")

    def show_disconnect_dialog(self):
        if not self.connections:
            QMessageBox.warning(self, "無連接", "當前沒有活動的連接")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("選擇要中斷的連接")
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for host in self.connections.keys():
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
        if host in self.connections:
            success, error = disconnect_from_as400(self.connections[host])
            if success:
                del self.connections[host]
                index = self.system_combo.findText(host)
                if index != -1:
                    self.system_combo.removeItem(index)
                QMessageBox.information(self, "斷開連接", f"已成功斷開與IBM i系統 {host} 的連接")
                
                if self.connections:
                    self.current_connection = next(iter(self.connections))
                    self.system_combo.setCurrentText(self.current_connection)
                    self.statusBar().showMessage(f"已切換到 {self.current_connection}")
                else:
                    self.current_connection = None
                    self.connect_button.setEnabled(True)
                    self.disconnect_button.setEnabled(False)
                    self.execute_button.setEnabled(False)
                    self.export_button.setEnabled(False)
                    self.statusBar().showMessage("已斷開所有連接")
            else:
                QMessageBox.warning(self, "斷開連接警告", f"斷開連接时发生错误：{error}")
        else:
            QMessageBox.warning(self, "無效的連接", f"找不到與 {host} 的連接")

    def switch_system(self, index):
        if index == 0:  # "選擇系統..." 項
            return
        
        selected_system = self.system_combo.currentText()
        if selected_system != self.current_connection:
            self.current_connection = selected_system
            self.statusBar().showMessage(f"已切換到系統: {selected_system}")

    def execute_query(self):
        if not self.current_connection:
            QMessageBox.warning(self, "無連接", "請先連接到個系統")
            return

        query = self.query_input.toPlainText()
        if not query:
            QMessageBox.warning(self, "查詢為空", "請輸入SQL查詢")
            return

        result, error = execute_query(self.connections[self.current_connection], query)
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

        file_path, _ = QFileDialog.getSaveFileName(self, "保存Excel文件", "", "Excel Files (*.xlsx)")
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
        if not self.user_managers or self.current_connection not in self.user_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 UserManager 未初始化")
            return
        self.stacked_widget.setCurrentWidget(self.user_manager_page)
        self.switch_button.setText('返回主界面')

    def switch_to_job_manager(self):
        if not self.job_managers or self.current_connection not in self.job_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")
            return
        self.stacked_widget.setCurrentWidget(self.job_manager_page)
        self.switch_button.setText('返回主界面')

    def closeEvent(self, event):
        for conn in self.connections.values():
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
        
        layout.addLayout(button_layout)
        
        self.refresh_user_list()

        refresh_button = QPushButton("刷新用戶列表")
        refresh_button.clicked.connect(self.refresh_user_list)
        layout.addWidget(refresh_button)

    def refresh_user_list(self):
        if not self.current_connection or self.current_connection not in self.user_managers:
            self.user_table.setRowCount(0)
            self.user_table.setColumnCount(0)
            return
        
        users = self.user_managers[self.current_connection].list_users()
        if users:
            columns, data = users
            self.user_table.setColumnCount(len(columns))
            self.user_table.setRowCount(len(data))
            self.user_table.setHorizontalHeaderLabels(columns)
            
            for row, row_data in enumerate(data):
                for col, value in enumerate(row_data):
                    self.user_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.user_table.resizeColumnsToContents()
        else:
            self.user_table.setRowCount(0)
            self.user_table.setColumnCount(0)

    def create_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("新建用戶")
        layout = QVBoxLayout(dialog)

        username_input = QLineEdit()
        username_input.setPlaceholderText("用戶名")
        layout.addWidget(username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("密碼")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_input)

        description_input = QLineEdit()
        description_input.setPlaceholderText("描述（可選）")
        layout.addWidget(description_input)

        authority_input = QComboBox()
        authority_input.addItems(["*USER", "*SECADM", "*ALLOBJ"])
        layout.addWidget(QLabel("權限:"))
        layout.addWidget(authority_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = username_input.text()
            password = password_input.text()
            description = description_input.text()
            authority = authority_input.currentText()
            if username and password:
                try:
                    self.user_managers[self.current_connection].create_user(username, password, description, authority)
                    QMessageBox.information(self, "成功", f"用戶 {username} 創建成功")
                    self.refresh_user_list()
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"創建用戶失敗: {str(e)}")
            else:
                QMessageBox.warning(self, "輸入錯誤", "用戶名和密碼不能為空")

    def delete_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("刪除用戶")
        layout = QVBoxLayout(dialog)

        username_input = QLineEdit()
        username_input.setPlaceholderText("要刪除的用戶名")
        layout.addWidget(username_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = username_input.text()
            if username:
                try:
                    self.user_managers[self.current_connection].delete_user(username)
                    QMessageBox.information(self, "成功", f"用戶 {username} 刪除成功")
                    self.refresh_user_list()
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"刪除用戶失敗: {str(e)}")
            else:
                QMessageBox.warning(self, "輸入錯誤", "用戶名不能為空")

    def change_password_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改密碼")
        layout = QVBoxLayout(dialog)

        username_input = QLineEdit()
        username_input.setPlaceholderText("用戶名")
        layout.addWidget(username_input)

        new_password_input = QLineEdit()
        new_password_input.setPlaceholderText("新密碼")
        new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(new_password_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = username_input.text()
            new_password = new_password_input.text()
            if username and new_password:
                try:
                    self.user_managers[self.current_connection].change_password(username, new_password)
                    QMessageBox.information(self, "成功", f"用戶 {username} 的密碼已成功修改")
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"修改密碼失敗: {str(e)}")
            else:
                QMessageBox.warning(self, "輸入錯誤", "用戶名和新密碼不能為空")

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
        if not self.job_managers or self.current_connection not in self.job_managers:
            QMessageBox.warning(self, "錯誤", "未連接到系統或 JobManager 未初始化")
            return
        
        jobs = self.job_managers[self.current_connection].list_active_jobs()
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
        selected_items = self.job_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "錯誤", "請先選擇一個作業")
            return
        job_name = selected_items[0].text()
        try:
            self.job_managers[self.current_connection].end_job(job_name)
            QMessageBox.information(self, "成功", f"作業 {job_name} 已成功結束")
            self.refresh_job_list()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"結束作業失敗: {str(e)}")

    def hold_selected_job(self):
        selected_items = self.job_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "錯誤", "請先選擇一個作業")
            return
        job_name = selected_items[0].text()
        try:
            self.job_managers[self.current_connection].hold_job(job_name)
            QMessageBox.information(self, "成功", f"作業 {job_name} 已成功暫停")
            self.refresh_job_list()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"暫停作業失敗: {str(e)}")

    def release_selected_job(self):
        selected_items = self.job_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "錯誤", "請先選擇一個作業")
            return
        job_name = selected_items[0].text()
        try:
            self.job_managers[self.current_connection].release_job(job_name)
            QMessageBox.information(self, "成功", f"作業 {job_name} 已成功釋放")
            self.refresh_job_list()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"釋放作業失敗: {str(e)}")