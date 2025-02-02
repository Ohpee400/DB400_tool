import jaydebeapi
<<<<<<< Updated upstream
=======
import os
import logging  # 添加日誌模組
from PySide6.QtWidgets import QMessageBox
>>>>>>> Stashed changes

jt400_path = "/Users/clark/Desktop/DDSC/Clark文件/13-JavaCode/jt400.jar"

class AS400Connector:
    def __init__(self):
        self.connections = {}
        self.current_connection = None

    def connect_to_as400(self, host, user, password):
        try:
            connection_string = f"jdbc:as400://{host}"
            connection = jaydebeapi.connect("com.ibm.as400.access.AS400JDBCDriver",
                                            connection_string,
                                            [user, password],
                                            jt400_path)
            self.connections[host] = connection
            self.current_connection = host
            return connection, None
        except Exception as e:
            return None, str(e)

    def disconnect_from_as400(self, host):
        if host in self.connections:
            try:
                self.connections[host].close()
                del self.connections[host]
                if self.connections:
                    self.current_connection = next(iter(self.connections))
                else:
                    self.current_connection = None
                return True, None
            except Exception as e:
                return False, str(e)
        else:
            return False, "找不到指定的連接"

    def switch_system(self, selected_system):
        if selected_system in self.connections:
            self.current_connection = selected_system
            return True
        return False

    def execute_query(self, query):
        if not self.current_connection:
            return None, "沒有活動的連接"
        try:
            with self.connections[self.current_connection].cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
                return (columns, result), None
        except Exception as e:
            return None, str(e)

# 保留原有的獨立函數，以保持向後兼容性
def connect_to_as400(host, user, password):
    connector = AS400Connector()
    return connector.connect_to_as400(host, user, password)

def disconnect_from_as400(connection):
    try:
        connection.close()
        return True, None
    except Exception as e:
        return False, str(e)

def execute_query(connection, query):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchall()
            return (columns, result), None
    except Exception as e:
        return None, str(e)