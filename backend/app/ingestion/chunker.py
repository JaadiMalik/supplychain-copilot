def split_text(
    text: str,
    chunk_size: int = 120,
    overlap: int = 25,
) -> list[str]:

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk_words = words[start:end]

        chunk = " ".join(chunk_words)

        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks