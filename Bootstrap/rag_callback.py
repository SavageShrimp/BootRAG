from langchain_core.callbacks import BaseCallbackHandler


class CustomCallbackHandler:
    def __init__(self):
        pass

    def on_message(self, message: str) -> None:
        print(message)

    def on_error(self, error: str) -> None:
        print(f"Error: {error}")

    def raise_error(self, error: str) -> None:
        print(f"Error: {error}")

    def ignore_llm(self) -> bool:
        return False

class MyCustomHandler(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.tokens.append(token)

    def get_tokens(self):
        return self.tokens

    def on_error(self, error: str) -> None:
        print(f"Error: {error}")

    def raise_error(self, error: str) -> None:
        print(f"Error: {error}")
