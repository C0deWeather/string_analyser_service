#!/usr/bin/env python3
"""SQLite version of DBStorage — stores DB inside a /data folder"""

import sqlite3
from sqlite3 import Error



class DBStorage:
    """A class to manage SQLite database connections and operations."""
    __db_path = "data.db"
    __conn = None
    __cursor = None
  
    @classmethod
    def reload(cls):
        """Create or reload the database connection."""
        try:
            # Connect (SQLite will create the .db file if it doesn’t exist)
            cls.__conn = sqlite3.connect(cls.__db_path, check_same_thread=False)
            cls.__cursor = cls.__conn.cursor()
        except Error as e:
            print(f"Error connecting to database: {e}")

    @classmethod
    def execute(cls, query, params=()):
        """Execute a SQL query with optional parameters."""
        try:
            cls.__cursor.execute(query, params)
            cls.__conn.commit()
        except Error as e:
            print(f"Error executing query: {e}")

    @classmethod
    def fetchall(cls, query, params=()):
        """Run a SELECT query and return all rows."""
        try:
            cls.__cursor.execute(query, params)
            return cls.__cursor.fetchall()
        except Error as e:
            print(f"Error fetching data: {e}")
            return []

    def close(cls):
        """Close the database connection."""
        if cls.__conn:
            cls.__conn.close()
