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

    def get_job_details(self, job_name):
        """獲取指定作業的詳細信息"""
        query = f"""
        SELECT *
        FROM TABLE(QSYS2.ACTIVE_JOB_INFO(JOB_NAME_FILTER => '{job_name}'))
        """
        return self._execute_query(query)

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
