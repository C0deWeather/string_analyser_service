create_tables_sql = """
CREATE TABLE IF NOT EXISTS analysed_strings (
    id TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS string_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    length INTEGER,
    is_palindrome BOOLEAN,
    unique_characters INTEGER,
    word_count INTEGER,
    string_id TEXT NOT NULL UNIQUE,
    FOREIGN KEY (string_id) REFERENCES analysed_strings(id)
);

CREATE TABLE IF NOT EXISTS character_frequency_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    string_id TEXT,
    character TEXT,
    frequency INTEGER,
    FOREIGN KEY (string_id) REFERENCES analysed_strings(id)
);
"""

insert_analysed_string_sql = """
INSERT INTO analysed_strings (id, value, created_at) VALUES (?, ?, ?);
"""
insert_string_properties_sql = """
INSERT INTO string_properties (length, is_palindrome, unique_characters, word_count, string_id)
VALUES (?, ?, ?, ?, ?);