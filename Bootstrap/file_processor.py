import os
from vector_database_storer import VectorDatabaseStorer
from web_page_fetcher import parse_html, split_text_into_chunks
from vector_database_storer import VectorDatabaseStorer
from database_to_rag import DatabaseToRagConverter

class FileProcessor:
    def __init__(self, db_path):
        self.db_path = db_path

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        text = parse_html(html_content)
        chunks = split_text_into_chunks(text)

        storer = VectorDatabaseStorer(self.db_path)
        storer.store_chunks(chunks)
        storer.close()

    def convert_to_rag_format(self):
        converter = DatabaseToRagConverter(self.db_path)
        rag_format = converter.convert_to_rag_format()
        converter.close()

        return rag_format

