from similarity import Similarity
from llm_evaluator import LlmEvaluator
from vector_database_storer import VectorDatabaseStorer
from typing import Generator
import queue
from threading import Thread
import logging
import os
import json

logging.basicConfig(level=logging.DEBUG)

# Load configuration from JSON file
config_path = "config.json"

if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

llm_model_path = config["llm_model_path"]
n_gpu_layers = config["n_gpu_layers"]
n_batch = config["n_batch"]
n_ctx = config["n_ctx"]
f16kv = config["f16kv"]


class RagPipeline:
    def __init__(self, db_path, llm, embed_model):
        self.db_path = db_path
        self.llm = llm
        self.embed_model = embed_model
        self.similarity = Similarity(self.db_path)

    def store_chunks(self, name, text):
        import hashlib
        from web_page_fetcher import split_text_into_chunks
        chunks = split_text_into_chunks(text)
        # Create SHA-256 hash of the text
        sha = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # Store the chunks with the documentid
        storer = VectorDatabaseStorer(self.db_path)
        storer.store_chunks_with_documentid(name, sha, chunks)
        storer.close()

        logging.debug("Chunks stored in database.")

    def fetch_rag_format(self):
        rag_format = self.similarity.fetch_chunks()
        logging.debug("RAG format fetched.")
        return "\n".join(rag_format)

    def generate_response(self, query: str, top_n: int = 5) -> str:
        try:
            # Get the most similar chunks with their documentident
            similar = self.similarity.get_most_similar_chunks(query, top_n=top_n)

            # Format the chunks into a single string, starting with the query
            # and including each chunk on a new line without the document ID
            formatted = query + "\n" + "\n".join([chunk for item in similar for chunk in item.chunks])

            formatted = formatted[:n_ctx]

            # Evaluate the response using the LLM
            evaluator = LlmEvaluator(self.embed_model, self.llm)
            response = evaluator.evaluate_data(formatted, self.db_path)

            logging.debug("Response generated using LLM.")
            print(response)

            return response
        except Exception as e:
            logging.error(f"Error in generate_response: {e}")
            return ""

    def stream_response(self, query: str, top_n: int = 5) -> Generator:
        try:
            # Get the most similar chunks with their documentident
            similar = self.similarity.get_most_similar_chunks(query, top_n=top_n)

            # Format the chunks into a single string, starting with the query
            # and including each chunk on a new line without the document ID
            formatted = query + "\n" + "\n".join([chunk for item in similar for chunk in item.chunks])

            formatted = formatted[:n_ctx]

            # Use the LLM's streaming capability
            generator = self.llm.stream(formatted)  # Ensure the LLM has a stream method

            print("about to start yielding tokens")

            # Process tokens as they arrive
            for token in generator:
                print(token)
                yield token

        except Exception as e:
            logging.error(f"Error in stream_response: {e}")
            raise
