import jaydebeapi

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
