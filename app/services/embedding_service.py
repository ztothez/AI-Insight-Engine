from together import Together
from dotenv import load_dotenv
import os

load_dotenv()

def get_embedding(text: str) -> list[float]:
    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
    response = client.embeddings.create(
        model="intfloat/multilingual-e5-large-instruct",
        input=text
    )
    return response.data[0].embedding