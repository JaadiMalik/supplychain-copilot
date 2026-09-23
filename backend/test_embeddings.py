from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

text = "ABC Supplier payment terms are Net 60 days."

response = client.embeddings.create(
    model="text-embedding-nomic-embed-text-v1.5@q8_0",
    input=text
)

embedding = response.data[0].embedding

print("Embedding created!")
print("Dimensions:", len(embedding))
print("First 10 values:", embedding[:10])