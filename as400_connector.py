import jaydebeapi

jt400_path = "/Users/clark/Desktop/DDSC/Clark文件/13-JavaCode/jt400.jar"

def connect_to_as400(host, user, password):
    try:
        connection_string = f"jdbc:as400://{host}"
        connection = jaydebeapi.connect("com.ibm.as400.access.AS400JDBCDriver",
                                        connection_string,
                                        [user, password],
                                        jt400_path)
        return connection, None
    except Exception as e:
        return None, str(e)

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