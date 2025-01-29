from flask import Flask, request, jsonify, stream_with_context
from rag_pipeline import RagPipeline
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from embeddings import embeddings
from flask import send_from_directory
import json
import os
import requests
from queue import Queue
from threading import Thread

import logging
from logging.config import dictConfig
import torch

# Load configuration from JSON file
config_path = "config.json"

if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

llm_model_path = config.get("llm_model_path")
n_gpu_layers = config.get("n_gpu_layers", 0)
n_batch = config.get("n_batch", 8)
n_ctx = config.get("n_ctx", 5000)
f16kv = config.get("f16kv", False)
db_path = config.get("db_path")
file_path = config.get("file_path")
port = config.get("port", 5000)

# Ensure f16kv is a boolean
if isinstance(f16kv, str):
    f16kv = f16kv.lower() in ['true', '1', 't']

# Configure logging
dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
})


class GeneratorManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeneratorManager, cls).__new__(cls)
        return cls._instance



# Initialize embeddings
embed_model = embeddings.get_embeddings()

llm = LlamaCpp(
    model_path=llm_model_path,
    n_gpu_layers=n_gpu_layers,
    n_batch=n_batch,
    n_ctx=n_ctx,
    f16kv=f16kv,
    streaming=True,
    verbose=False
)

# Initialize the RagPipeline
pipeline = RagPipeline(db_path, llm, embed_model)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_file():
    data = request.get_json()
    name = data.get('name')
    text = data.get('text')
    print(name, " ", text)
    try:
        pipeline.store_chunks(name, text)
        processed_text = f'Processed text chunks - {name}'
        return jsonify({'text': processed_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_response():
    @stream_with_context
    def stream_response():
        data = request.get_json()
        text = data.get('text')

        try:
            # Use the pipeline to process the text and get the response generator
            generator = pipeline.stream_response(text)

            # Use a queue to collect tokens
            token_queue = Queue()

            # Start a thread to process tokens
            def token_handler():
                for token in generator:
                    print(token)
                    token_queue.put(token)
                token_queue.put(None)  # Signal end of stream

            thread = Thread(target=token_handler)
            thread.start()

            while True:
                token = token_queue.get()
                if token is None:
                    break
                yield jsonify({'token': token}).data + b'\n'

            thread.join()
        except Exception as e:
            yield jsonify({'error': str(e)}).data + b'\n'
            raise

    return app.response_class(stream_response(), mimetype='application/json')

@app.route('/embeddings', methods=['POST'])
def get_embeddings():
    data = request.get_json()
    text = data.get('text')

    try:
        # Generate embeddings for the input text
        embedding = embed_model.embed_text([text])

        # Convert the embedding to a list and return as JSON
        return jsonify({'embedding': embedding[0].tolist()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

# Create messages
msg1 = Message(role="system", content="You are a helpful assistant.")
msg2 = Message(role="user", content="How can I help you today?")
prompt = "You are an AI assistant"

# Create config data
config_data = {
    "messages": [
    ],
    "prompt": '',  # Add the 'prompt' parameter
    "stream": True,
    "cache_prompt": True,
    "samplers": "edkypmxt",
    "temperature": 0.8,
    "dynatemp_range": 0,
    "dynatemp_exponent": 1,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "typical_p": 1,
    "xtc_probability": 0,
    "xtc_threshold": 0.1,
    "repeat_last_n": 64,
    "repeat_penalty": 1,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "dry_multiplier": 0,
    "dry_base": 1.75,
    "dry_allowed_length": 2,
    "dry_penalty_last_n": -1,
    "max_tokens": -1,
    "timings_per_token": False
}

config_data["messages"] = [ { "role": "system", "content": "You are an LLM expert who provides insight and ideas on the creation of LLM systems. You can provide help with coding design and prompt generation" }]
global_buffer = ""

"""
def process_data(string):
    global global_buffer
    if isinstance(string, bytes):
        # If the input is bytes, decode it to a string
        string = string.decode('utf-8')
    # Now string is a str, proceed
    if string.startswith("data: "):
        stripped = string[6:]
    else:
        stripped = string
    # Check if stripped ends with "\n\n" (two newlines)
    if stripped.endswith("\n\n"):
        stripped = stripped.rstrip("\n")
        # Assign to global_buffer
        global_buffer = stripped
        return True
    else:
        if string.startswith("data: "):
            global_buffer = stripped
        else:
            global_buffer += stripped
        return False
"""

class DataAccumulator:
    buffer = b""

    def accumulate_data(self, data):
        if isinstance(data, bytes):
            data_str = data.decode('utf-8')
        else:
            data_str = data

        if data_str.startswith("data: "):
            temp = self.buffer
            self.buffer = data
        else:
            self.buffer += data

        if self.buffer and self.buffer.endswith(b"\n\n"):
            result = self.buffer.strip(b"\n\n").lstrip(b"data: ")
            self.buffer = b""
            return (result.decode('utf-8'), True)
        else:
            return (self.buffer, False)

@app.route('/completions', methods=['POST'])
@stream_with_context
def stream_completions():
    data = request.get_json()
    text = data.get('text')
    content_buffer = ''

    config_data["prompt"] = text

    print(config_data)

    # Initialize the data accumulator
    data_accumulator = DataAccumulator()

    try:
        # Use the LlamaCpp model to stream the completion
        GeneratorManager().generator = requests.post("http://192.168.1.100:8080/completions", json=config_data, stream=True)

        # Use a queue to collect tokens
        token_queue = Queue()

        # Start a thread to process tokens
        def token_handler():
            if GeneratorManager().generator is not None:
                for token in GeneratorManager().generator:
                    token_queue.put(token)

        thread = Thread(target=token_handler)
        thread.start()

        while True:
            token = token_queue.get()
            if token is None:
                break

            # Process the token and get both the updated buffer and the boolean result
            global_buffer, should_yield = data_accumulator.accumulate_data(token)
            print(global_buffer)

            # Decode the buffer to string before yielding
            if should_yield:
                # yield jsonify({'data': global_buffer}).data + b'\n'
                yield global_buffer
                # data_accumulator.buffer = b""  # Clear the buffer after yielding

        thread.join()

        config_data["messages"].append({"role": "user", "content": config_data["prompt"]})
        config_data["messages"].append({"role": "system", "content": global_buffer})

    except Exception as e:
        yield jsonify({'error': str(e)}).data + b'\n'
        raise

@app.route('/close')
def close():
    if GeneratorManager().generator:
        for _ in GeneratorManager().generator:
            pass
        GeneratorManager().generator.close()
    return "Generator closed."


if __name__ == '__main__':
    app.run(debug=True)
