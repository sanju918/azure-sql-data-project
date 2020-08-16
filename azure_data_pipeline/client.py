
import time
import pyodbc
import textwrap

from typing import List
from typing import Dict
from typing import Union

from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.sql.models import Database as AzureDatabase
from azure.mgmt.sql.models import Server as AzureServer


class AzureSQLClient():

    def __init__(self, client_id: str, client_secret: str, subscription_id: str, tenant_id: str, username: str, password: str) -> None:
        """Initializes the `AzureSQLClient` object.

        Arguments:
        ----
        client_id (str): Your Azure Client ID.

        client_secret (str): Your Azure Client Secret.

        subscription_id (str): Your Azure Subscription ID.

        tenant_id (str): Your Azure Tenant ID.

        username (str): The username of the Azure SQL Server.

        password (str): The password of the Azure SQL Server.
        """

        self.connected = False
        self.authenticated = False

        # Define the client info.
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.server_username = username
        self.server_password = password

        # Create your Credential Object.
        self._credentials = None
        self._create_credential()

        # Create your SQL Management Client Object.
        self._sql_management_client = None
        self._create_sql_management_client()

        self._server_name = None
        self._resource_group = None
        self._database_name = None

        # Define properties related to connection.
        self.connection_object: pyodbc.Connection = None
        self.cursor_object: pyodbc.Cursor = None

    def __repr__(self):
        """String representation of our `AzureSQLClient` instance."""

        # define the string representation
        str_representation = '<AzureSQLClient (connected={login_state}, authorized={auth_state})>'.format(
            login_state=self.connected,
            auth_state=self.authenticated
        )

        return str_representation

    def __del__(self):
        """Defines what to do when the `AzureSQLClient` is deleted."""

        # If we have a cursor object or connection object.
        if self.cursor_object or self.connection_object:

            # Commit all the transactions.
            self.cursor_object.commit()

            # Close the Cursor.
            self.cursor_object.close()

            # Close the connection.
            self.connection_object.close()

    def _create_credential(self) -> None:
        """Creates a credential object.

        Overview:
        ----
        Initalizes the `ServicePrincipalCredentials` object used 
        to connect to different Azure services.
        """

        # Initialize it.
        credential = ServicePrincipalCredentials(
            tenant=self.tenant_id,
            client_id=self.client_id,
            secret=self.client_secret
        )

        self._credentials = credential
        self.connected = True

    def _create_sql_management_client(self) -> None:
        """Creates a `SqlManagementClient` object.

        Overview:
        ----
        Initalizes the `SqlManagementClient` object used 
        to manage different SQL Server Objects.
        """

        # Initialize it.
        sql_management_client = SqlManagementClient(
            credentials=self.credentials,
            subscription_id=self.subscription_id
        )

        self._sql_management_client = sql_management_client
        self.authenticated = True

    @property
    def credentials(self) -> ServicePrincipalCredentials:
        """Returns the credential object.

        Returns:
        ----
        ServicePrincipalCredentials: A credential object with the authentication
            items.
        """

        return self._credentials

    @property
    def sql_management_client(self) -> SqlManagementClient:
        """Returns the SQL Management Client object.

        Returns:
        ----
        SqlManagementClient: Our management client used to interact with the
            different Azure SQL Objects.
        """

        return self._sql_management_client

    @property
    def server_name(self) -> str:
        """Used to Grab the Server Name.

        Returns:
        ----
        str: The Server Name.
        """
        return self._server_name

    @server_name.setter
    def server_name(self, value: str) -> None:
        """Used to set the Server Name.

        Arguments:
        ----
        value (str): The name of the Server.
        """
        self._server_name = value

    @property
    def resource_group_name(self) -> str:
        """Used to Grab the Resource Group Name.

        Returns:
        ----
        str: The Resource Group Name.
        """
        return self._resource_group

    @resource_group_name.setter
    def resource_group_name(self, value: str) -> None:
        """Used to set the Resource Group Name.

        Arguments:
        ----
        value (str): The name of the Resource Group.
        """
        self._resource_group = value

    @property
    def database_name(self) -> str:
        """Used to Grab the Database Name.

        Returns:
        ----
        str: The Database Name.
        """
        return self._database_name

    @database_name.setter
    def database_name(self, value: str) -> None:
        """Used to set the Database Name.

        Arguments:
        ----
        value (str): The name of the Database.
        """
        self._database_name = value

    def get_server(self, resource_group: str = None, server_name: str = None) -> AzureServer:
        """Returns the Server from the specified Resource Group.

        Arguments:
        ----
        resource_group (str, optional): The resource group name. Defaults to None.

        server_name (str, optional): The name of the server. Defaults to None.

        Returns:
        ----
        AzureServer: An AzureServer model.
        """

        # Grab the inputs if they don't exist.
        if self._resource_group:
            resource_group = self.resource_group_name
        else:
            resource_group = resource_group

        if self._server_name:
            server_name = self.server_name
        else:
            server_name = server_name

        # Grab the server.
        server = self.sql_management_client.servers.get(
            resource_group_name=resource_group,
            server_name=server_name
        )

        return server

    def get_database(self, resource_group: str = None, server_name: str = None, database_name: str = None) -> AzureDatabase:
        """Returns the Database from the specified Server and Resource Group.

        Arguments:
        ----
        resource_group (str, optional): The resource group name. Defaults to None.

        server_name (str, optional): The name of the server. Defaults to None.

        database_name (str, optional): The name of the database. Defaults to None.

        Returns:
        ----
        AzureDatabase: An AzureDatabase model.
        """

        # Grab the inputs if they don't exist.
        if self._resource_group:
            resource_group = self.resource_group_name
        else:
            resource_group = resource_group

        if self._server_name:
            server_name = self.server_name
        else:
            server_name = server_name

        if self._database_name:
            database_name = self.database_name
        else:
            database_name = database_name

        # Grab the database.
        database = self.sql_management_client.databases.get(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name
        )

        return database

    def connect_to_database(self, server: str, database: str, driver: str = None) -> pyodbc.Connection:
        """Creates a connection to the SQL Database and opens the Cursor.

        Arguments:
        ----
        server (str): The server name.

        database (str): The database name.

        driver (str, optional): The ODBC SQL Driver to be used. Defaults to None.

        Returns:
        ----
        pyodbc.Connection: A connection object for the database.
        """

        # 'trading-robot.database.windows.net,1433'

        # Create the Server String.
        server = '{server}.database.windows.net,1433'.format(server=server)

        # If a driver was passed through, use that.
        if driver:
            driver = driver
        else:
            driver = '{ODBC Driver 17 for SQL Server}'

        # Create the connection String.
        connection_string = textwrap.dedent('''
            Driver={driver};
            Server={server};
            Database={database};
            Uid={username};
            Pwd={password};
            Encrypt=yes;
            TrustServerCertificate=no;
            Connection Timeout=30;
        '''.format(driver=driver, server=server, database=database, username=self.server_username, password=self.server_password))

        # Create a new connection.
        try:
            cnxn = pyodbc.connect(connection_string)
        except pyodbc.OperationalError:
            time.sleep(2)
            cnxn = pyodbc.connect(connection_string)

        # Set the object property.
        self.connection_object = cnxn

        # Create the cursor.
        self._create_cursor()

        return self.connection_object

    def _create_cursor(self) -> None:
        """Creates the `Cursor` Object from the Database Connection. """

        self.cursor_object = self.connection_object.cursor()


# with pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
#     with conn.cursor() as cursor:
#         cursor.execute("SELECT TOP 20 pc.Name as CategoryName, p.name as ProductName FROM [SalesLT].[ProductCategory] pc JOIN [SalesLT].[Product] p ON pc.productcategoryid = p.productcategoryid")
#         row = cursor.fetchone()
#         while row:
#             print (str(row[0]) + " " + str(row[1]))
#             row = cursor.fetchone()