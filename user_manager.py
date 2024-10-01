import jaydebeapi
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog, QLineEdit

class UserManager:
    def __init__(self, connection):
        self.connection = connection

    def list_users(self):
        """列出所有使用者"""
        query = """
        SELECT USER_NAME, STATUS, PREVIOUS_SIGNON, PASSWORD_CHANGE_DATE
        FROM QSYS2.USER_INFO
        ORDER BY USER_NAME
        """
        return self._execute_query(query)

    def create_user(self, username, password, description="", authority="*USER"):
        """創建新使用者"""
        create_query = f"CREATE USER {username} IDENTIFIED BY '{password}'"
        self._execute_query(create_query)
        
        if description:
            desc_query = f"CHGUSRPRF USRPRF({username}) TEXT('{description}')"
            self._execute_query(desc_query)
        
        auth_query = f"GRTOBJAUT OBJ({username}) OBJTYPE(*USRPRF) USER(*PUBLIC) AUT({authority})"
        self._execute_query(auth_query)

    def delete_user(self, username):
        """刪除使用者"""
        query = f"DROP USER {username}"
        self._execute_query(query)

    def change_password(self, username, new_password):
        """更改使用者密碼"""
        query = f"SET PASSWORD {username} = '{new_password}'"
        self._execute_query(query)

    def disable_user(self, username):
        """停用使用者帳號"""
        query = f"CHGUSRPRF USRPRF({username}) STATUS(*DISABLED)"
        self._execute_query(query)

    def enable_user(self, username):
        """啟用使用者帳號"""
        query = f"CHGUSRPRF USRPRF({username}) STATUS(*ENABLED)"
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

class UserManagerGUI(QWidget):
    def __init__(self, parent, user_manager):
        super().__init__(parent)
        self.parent = parent
        self.user_manager = user_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 創建按鈕
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新用戶列表')
        self.create_button = QPushButton('創建用戶')
        self.delete_button = QPushButton('刪除用戶')
        self.change_password_button = QPushButton('更改密碼')

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.change_password_button)

        layout.addLayout(button_layout)

        # 創建表格
        self.user_table = QTableWidget()
        layout.addWidget(self.user_table)

        # 連接按鈕信號
        self.refresh_button.clicked.connect(self.refresh_user_list)
        self.create_button.clicked.connect(self.create_user_dialog)
        self.delete_button.clicked.connect(self.delete_user_dialog)
        self.change_password_button.clicked.connect(self.change_password_dialog)

        # 初始化用戶列表
        self.refresh_user_list()

    def refresh_user_list(self):
        result = self.user_manager.list_users()
        if result:
            columns, data = result
            self.user_table.setColumnCount(len(columns))
            self.user_table.setRowCount(len(data))
            self.user_table.setHorizontalHeaderLabels(columns)

            for row, user_data in enumerate(data):
                for col, value in enumerate(user_data):
                    self.user_table.setItem(row, col, QTableWidgetItem(str(value)))

            self.user_table.resizeColumnsToContents()
        else:
            QMessageBox.warning(self, "錯誤", "無法獲取用戶列表")

    def get_selected_user(self):
        selected_items = self.user_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "請先選擇一個用戶")
            return None
        return selected_items[0].text()  # 假設第一列是用戶名

    def create_user_dialog(self):
        username, ok = QInputDialog.getText(self, "創建用戶", "輸入用戶名:")
        if ok and username:
            password, ok = QInputDialog.getText(self, "創建用戶", "輸入密碼:", QLineEdit.Password)
            if ok and password:
                description, ok = QInputDialog.getText(self, "創建用戶", "輸入描述 (可選):")
                if ok:
                    self.user_manager.create_user(username, password, description)
                    self.refresh_user_list()

    def delete_user_dialog(self):
        username = self.get_selected_user()
        if username:
            confirm = QMessageBox.question(self, "確認", f"確定要刪除用戶 {username} 嗎？",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.user_manager.delete_user(username)
                self.refresh_user_list()

    def change_password_dialog(self):
        username = self.get_selected_user()
        if username:
            new_password, ok = QInputDialog.getText(self, "更改密碼", "輸入新密碼:", QLineEdit.Password)
            if ok and new_password:
                self.user_manager.change_password(username, new_password)
                QMessageBox.information(self, "成功", "密碼已更改")
