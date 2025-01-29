import json
import os
from torch import cuda
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from rag_callback import CustomCallbackHandler, MyCustomHandler
from database_to_rag import DatabaseToRagConverter
from embeddings import embeddings
import logging

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

# Embeddings configuration
embed_model_id = 'sentence-transformers/all-MiniLM-L6-v2'

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

embed_model = HuggingFaceEmbeddings(
    model_name=embed_model_id,
    model_kwargs={'device': device},
    encode_kwargs={'device': device, 'batch_size': 32}
)

# LLM configuration
#callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
#callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
callback_manager = CallbackManager([MyCustomHandler()])

llm = LlamaCpp(
    model_path=llm_model_path,
    n_gpu_layers=n_gpu_layers,
    n_batch=n_batch,
    n_ctx=n_ctx,
    f16kv=f16kv,
    max_tokens=2000,
    callback_manager=callback_manager,
    verbose=False,
)

logging.basicConfig(level=logging.DEBUG)

class LlmEvaluator:
    def __init__(self, embed_model, llm):
        self.embed_model = embed_model
        self.llm = llm

    def evaluate_data(self, text, db_path):
        # Embed the text
        print("***", text, "***")
        embeddings = self.embed_model.embed_documents([text])

        #allbacks = [CustomCallbackHandler()]
        callbacks = [MyCustomHandler()]
        manager = CallbackManager(handlers=callbacks)
        #self.llm = LlamaCpp( ... callbacks=manager ... )

        # And when calling the model:
        #with manager:
            # Generate a response using the LLM
        response = self.llm.invoke(text)

        # Close the database connection
        converter = DatabaseToRagConverter(db_path)
        converter.close()

        return embeddings, response

