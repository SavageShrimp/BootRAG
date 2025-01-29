import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)

class VectorDatabaseStorer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        # Enable foreign key constraints
        self.conn.execute("PRAGMA foreign_keys = 1")

    def _create_tables(self):
        cursor = self.conn.cursor()

        # Create chunks table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documentid INTEGER NOT NULL,
                chunk TEXT NOT NULL,
                FOREIGN KEY(documentid) REFERENCES document_info(id)
            )
        ''')

        # Create document_info table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documentident TEXT NOT NULL,
                documenthash TEXT NOT NULL
            )
        ''')

        self.conn.commit()
        logging.debug("Tables created successfully.")

    def store_chunks(self, name, document_hash, chunks):
        cursor = self.conn.cursor()

        # Insert into document_info
        cursor.execute('''
            INSERT INTO document_info (documentident, documenthash)
            VALUES (?, ?)
        ''', (name, document_hash))

        # Get the documentid from the last insertion
        documentid = cursor.lastrowid

        # Prepare the data for chunks as a list of tuples
        chunk_data = [(documentid, chunk) for chunk in chunks]

        # Insert multiple chunks with documentid
        cursor.executemany(
            'INSERT INTO chunks (documentid, chunk) VALUES (?, ?)',
            chunk_data
        )

        self.conn.commit()
        logging.debug(f"Stored {len(chunks)} chunks successfully.")

    def store_chunks_with_documentid(self, name, document_hash, chunks):
        cursor = self.conn.cursor()

        # Insert into document_info
        cursor.execute('''
            INSERT INTO document_info (documentident, documenthash)
            VALUES (?, ?)
        ''', (name, document_hash))

        # Get the documentid from the last insertion
        documentid = cursor.lastrowid

        # Prepare the data for chunks as a list of tuples
        chunk_data = [(documentid, chunk) for chunk in chunks]

        # Insert multiple chunks with documentid
        cursor.executemany(
            'INSERT INTO chunks (documentid, chunk) VALUES (?, ?)',
            chunk_data
        )

        self.conn.commit()
        logging.debug(f"Stored {len(chunks)} chunks successfully.")

    def close(self):
        self.conn.close()
        logging.debug("Database connection closed.")
