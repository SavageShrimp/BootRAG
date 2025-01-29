import sqlite3

class DatabaseToRagConverter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)

    def fetch_chunks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT chunk FROM chunks")
        chunks = cursor.fetchall()
        return [chunk[0] for chunk in chunks]

    def convert_to_rag_format(self):
        chunks = self.fetch_chunks()
        # Convert chunks to a format suitable for your RAG model
        # For example, join them into a single string
        rag_format = "\n".join(chunks)
        return rag_format

    def close(self):
        self.conn.close()

