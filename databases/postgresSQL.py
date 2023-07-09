import psycopg2
from psycopg2 import sql
from typing import List, Tuple, Any

class postgres:
    """
    This class is a wrapper of psycopg2 for basic database operations including reading, writing, updating, and deleting.
    
    Example:
    db_manager = DatabaseManager(database="my_database", user="my_user", password="my_password")
    db_manager.insert_data("my_table", {"column1": "value1", "column2": "value2"})
    data = db_manager.read_data("my_table", ["column1", "column2"])
    print(data)
    db_manager.update_data("my_table", {"column1": "new_value"}, "column2 = 'value2'")
    db_manager.delete_data("my_table", "column1 = 'new_value'")
    """
    def __init__(self, database: str, user: str, password: str, host: str = "127.0.0.1", port: str = "5432"):
        self.conn = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.conn.cursor()

    def read_data(self, table_name: str, columns: List[str]) -> List[Tuple[Any]]:
        """
        Read data from the specified columns of a table.

        :param table_name: the name of the table to read from.
        :param columns: a list of column names to read.
        :return: a list of tuples where each tuple corresponds to a row in the table.
        """
        query = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(',').join(map(sql.Identifier, columns)),
            sql.Identifier(table_name)
        )
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def insert_data(self, table_name: str, data_dict: dict):
        """
        Insert data into a table.

        :param table_name: the name of the table to insert into.
        :param data_dict: a dictionary where keys are column names and values are data to insert.
        """
        columns = data_dict.keys()
        values = data_dict.values()
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(',').join(map(sql.Identifier, columns)),
            sql.SQL(',').join(map(sql.Placeholder, columns))
        )
        self.cursor.execute(query, data_dict)
        self.conn.commit()

    def update_data(self, table_name: str, data_dict: dict, condition: str):
        """
        Update data in a table.

        :param table_name: the name of the table to update.
        :param data_dict: a dictionary where keys are column names and values are data to update.
        :param condition: a string of condition for updating. e.g. "column1 = 'value1' AND column2 = 'value2'"
        """
        set_statements = [f"{column} = %({column})s" for column in data_dict.keys()]
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(map(sql.SQL, set_statements)),
            sql.SQL(condition)
        )
        self.cursor.execute(query, data_dict)
        self.conn.commit()

    def delete_data(self, table_name: str, condition: str):
        """
        Delete data from a table.

        :paramtable_name: the name of the table to delete from.
        :param condition: a string of condition for deleting. e.g. "column1 = 'value1' AND column2 = 'value2'"
        """
        query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table_name),
            sql.SQL(condition)
        )
        self.cursor.execute(query)
        self.conn.commit()

    def __del__(self):
        """
        Close the database connection when the instance is deleted.
        """
        self.cursor.close()
        self.conn.close()
