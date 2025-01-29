import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

def fetch_web_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching the web page: {e}")
        return None

def parse_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style tags
        for script in soup(['script', 'style']):
            script.decompose()
        # Get text
        text = soup.get_text()
        return text
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None

def split_text_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=200,
        length_function=len,
    )
    try:
        chunks = text_splitter.split_text(text)
        return chunks
    except Exception as e:
        logging.error(f"Error splitting text into chunks: {e}")
        return []

