#!/usr/bin/env python3
from flask import abort
import sqlite3
from sqlite3 import Error
from models.sql_scripts import (
    create_tables_sql,
    insert_analysed_string_sql,
    insert_string_properties_sql,
    insert_character_frequency_map_sql,
)


class DBStorage:
    """A class to manage SQLite database connections and operations."""
    __db_path = "data.db"
    __conn = None
    __cursor = None
    
    def __init__(self):
        """Initialize the database connection."""
        self.reload()

        # create tables if they do not exist
        try:
            self.__cursor.executescript(create_tables_sql)
            self.__conn.commit()
        except Error as e:
            abort(500, str(e))
    
    @classmethod
    def reload(cls):
        """Create or reload the database connection."""
        try:
            # Connect (SQLite will create the .db file if it doesn’t exist)
            cls.__conn = sqlite3.connect(cls.__db_path, check_same_thread=False)
            cls.__cursor = cls.__conn.cursor()
        except Error as e:
            abort(500, str(e))

    @classmethod
    def execute(cls, query, params=()):
        """Execute a SQL query with optional parameters."""
        try:
            cls.__cursor.execute(query, params)
        except Error as e:
            cls.__conn.rollback()
            abort(500, str(e))

    @classmethod
    def fetchall(cls, query, params=()):
        """Run a SELECT query and return all rows."""
        try:
            cls.__cursor.execute(query, params)
            return cls.__cursor.fetchall()
        except Error:
            return []
    @classmethod
    def fetchone(cls, query, params=()):
        """Run a SELECT query and return a single row."""
        try:
            cls.__cursor.execute(query, params)
            return cls.__cursor.fetchone()
        except Error:
            return None

    @classmethod
    def get_analysed_string_by_value(cls, value):
        """Retrieve an analysed string record by its value."""
        query = "SELECT * FROM analysed_strings WHERE value = ?;"
        return cls.fetchone(query, (value,))

    @classmethod
    def get_all_analysed_strings(cls):
        query = "SELECT * FROM analysed_strings;"
        return cls.fetchall(query)

    @classmethod
    def save(cls):
        """Commit the current transaction."""
        try:
            cls.__conn.commit()
        except Error as e:
            abort(500, str(e))

    @classmethod
    def insert(cls, object):
        """Insert a new record into the database."""
        # analysed_string table insertion
        params = (object.id, object.string, object.created_at)
        cls.execute(insert_analysed_string_sql, params)

        # string_properties table insertion
        props = object.properties
        props_params = (
            props["length"],
            props["is_palindrome"],
            props["unique_characters"],
            props["word_count"],
            object.id
        )
        cls.execute(insert_string_properties_sql, props_params)

        # character_frequency_map table insertion
        freq_map = props["character_frequency_map"]
        for char, freq in freq_map.items():
            freq_params = (object.id, char, freq)
            cls.execute(insert_character_frequency_map_sql, freq_params)

        cls.save()

    @classmethod
    def delete_string(cls, string_id):
        """Delete a string and its related records from the database."""
        try:
            # Delete related records first
            cls.__cursor.execute("DELETE FROM character_frequency_map WHERE string_id = ?", (string_id,))
            cls.__cursor.execute("DELETE FROM string_properties WHERE string_id = ?", (string_id,))

            # Then delete the string itself
            cls.__cursor.execute("DELETE FROM analysed_strings WHERE id = ?", (string_id,))

            cls.save()

        except Exception as e:
            cls.__conn.rollback()
            abort(500, str(e))

    @classmethod
    def close(cls):
        """Close the database connection and cursor safely."""
        try:
            if cls.__cursor:
                cls.__cursor.close()
                cls.__cursor = None
            if cls.__conn:
                cls.__conn.close()
                cls.__conn = None
        except Exception as e:
            print(f"Error closing database: {e}")
