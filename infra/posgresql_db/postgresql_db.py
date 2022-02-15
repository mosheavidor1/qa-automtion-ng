import json

import allure
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from infra.allure_report_handler.reporter import Reporter
from infra.containers.postgresql_over_ssh_details import PostgresqlOverSshDetails
from infra.containers.ssh_details import SshDetails


class PostgresqlOverSshDb:

    def __init__(self,
                 ssh_details: SshDetails,
                 postgresql_details: PostgresqlOverSshDetails):

        self._ssh_details: SshDetails = ssh_details
        self._postgresql_details: PostgresqlOverSshDetails= postgresql_details
        self._engine = None
        self._session = None

    @property
    def session(self):
        return self._session

    @allure.step("Connect to postgresql DB Using SSH binding")
    def connect(self):
        """
        This method use to connect to postgresql DB via SSHTunnelForwarder since postgresql configuration allows
        to connect to the DB only from the machine itself (127.0.0.1) unless we change the configuration of it.
        """
        server = SSHTunnelForwarder((self._ssh_details.host_ip, int(self._ssh_details.port)),  # Remote server IP and SSH port
                                     ssh_username=self._ssh_details.user_name,
                                    ssh_password=self._ssh_details.password,
                                    remote_bind_address=(self._postgresql_details.server_ip, int(self._postgresql_details.server_port)))
        server.start()  # start ssh sever

        # connect to PostgreSQL
        local_port = str(server.local_bind_port)
        self._engine = create_engine(
            f'postgresql://{self._postgresql_details.user_name}:{self._postgresql_details.password}@{self._postgresql_details.server_ip}:{local_port}/{self._postgresql_details.db_name}')

        Session = sessionmaker(bind=self._engine, autocommit=True)
        self._session = Session()

    @allure.step("Disconnect from DB")
    def disconnect(self):
        if self._session is not None:
            self._session.close()

    @allure.step("Execute SQL command")
    def execute_sql_command(self, sql_cmd: str) -> list[dict]:
        """
        This method execute any sql query
        will return result only in case that "select" in the sql_cmd
        :param sql_cmd: sql query as string
        :return: list of dict with key as column_name, and value as data
        """

        if self._session is None:
            self.connect()

        if 'select' in sql_cmd.lower():
            results = self._session.execute(sql_cmd).fetchall()
            results_as_list_of_dicts = [{**row} for row in results]
            Reporter.attach_str_as_file(file_name='result', file_content=json.dumps(results_as_list_of_dicts, indent=4))
            return results_as_list_of_dicts

        self._session.execute(sql_cmd)

