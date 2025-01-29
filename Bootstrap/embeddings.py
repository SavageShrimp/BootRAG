from langchain_community.embeddings import HuggingFaceEmbeddings
import torch
import logging

logging.basicConfig(level=logging.DEBUG)

class _Embeddings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_Embeddings, cls).__new__(cls)
            cls._instance._embed_model = cls._initialize_embeddings()
        return cls._instance

    @staticmethod
    def _initialize_embeddings():
        embed_model_id = 'sentence-transformers/all-MiniLM-L6-v2'

        device = f'cuda:{torch.cuda.current_device()}' if torch.cuda.is_available() else 'cpu'

        try:
            embed_model = HuggingFaceEmbeddings(
                model_name=embed_model_id,
                model_kwargs={'device': device},
                encode_kwargs={'device': device, 'batch_size': 32}
            )
        except Exception as e:
            logging.error(f"Error initializing Hugging Face embeddings: {e}")
            return None

        logging.debug("Hugging Face embeddings initialized.")
        return embed_model

    def get_embeddings(self):
        return self._embed_model

# Create a singleton instance
embeddings = _Embeddings()

