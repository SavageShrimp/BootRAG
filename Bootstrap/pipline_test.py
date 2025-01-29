from rag_pipeline import RagPipeline
from llm_evaluator import embed_model, llm

def main():
    db_path = "chunks.db"  # Path to the SQLite database
    file_path = "example.html"  # Path to the HTML file
    query = "how do I set up an LLM pipeline"  # Query text to generate a response

    pipeline = RagPipeline(db_path, file_path, llm, embed_model)
    pipeline.process_file()
    response = pipeline.generate_response(query, top_n=5)

    print("Generated Response:")
    print(response)

if __name__ == "__main__":
    main()

