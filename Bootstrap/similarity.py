from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple
import sqlite3
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)

# Define a named tuple to hold the result
DocumentChunk = namedtuple('DocumentChunk', ['documentident', 'chunks'])

class Similarity:
    def __init__(self, db_path):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer()

    def fetch_chunks(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT chunk, documentid FROM chunks")
            chunks = cursor.fetchall()
            conn.close()
            return chunks
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []

    def get_tfidf_matrix(self, chunks):
        try:
            chunk_texts = [chunk for chunk, _ in chunks]
            return self.vectorizer.fit_transform(chunk_texts)
        except Exception as e:
            logging.error(f"Error computing TF-IDF matrix: {e}")
            return None

    def calculate_cosine_similarity(self, query, tfidf_matrix):
        try:
            query_vector = self.vectorizer.transform([query])
            cosine_scores = cosine_similarity(query_vector, tfidf_matrix)
            return cosine_scores.ravel()
        except Exception as e:
            logging.error(f"Error calculating cosine similarity: {e}")
            return None

    def get_most_similar_chunks(self, query: str, top_n: int = 5) -> list[DocumentChunk]:
        try:
            # Fetch chunks and their documentids
            chunks = self.fetch_chunks()
            if not chunks:
                logging.warning("No chunks found in the database.")
                return []

            # Group chunks by documentid
            grouped_chunks = {}
            for chunk, documentid in chunks:
                if documentid not in grouped_chunks:
                    grouped_chunks[documentid] = []
                grouped_chunks[documentid].append(chunk)

            # Format the result as named tuples
            result = []
            for documentid, chunk_list in grouped_chunks.items():
                # Get the documentident for this documentid
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT documentident FROM document_info WHERE id = ?", (documentid,))
                row = cursor.fetchone()
                documentident = row[0] if row else ""
                conn.close()

                # Create a DocumentChunk instance
                result.append(DocumentChunk(documentident=documentident, chunks=chunk_list))

            return result
        except Exception as e:
            logging.error(f"Error getting most similar chunks: {e}")
            return []
