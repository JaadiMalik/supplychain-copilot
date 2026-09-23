from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

# Test with a piece of our supplier contract
chunk = """
3. Price and Payment:
The total price for the Products is PKR__________.
Payment Terms: Payment shall be made according to the agreed terms.
"""

# Nomic works better for retrieval when we identify this as document text
text_for_embedding = f"search_document: {chunk}"

response = client.embeddings.create(
    model=MODEL,
    input=text_for_embedding
)

embedding = response.data[0].embedding

print("Embedding created successfully!")
print("Dimensions:", len(embedding))
print("First 10 values:", embedding[:10])