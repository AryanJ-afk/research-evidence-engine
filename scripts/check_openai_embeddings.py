from langchain_openai import OpenAIEmbeddings


def main():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        dimensions=1536,
        request_timeout=30,
        max_retries=1,
    )

    texts = [
        "Supervised learning uses labelled examples.",
        "Astronomers investigate the formation of galaxies.",
    ]

    vectors = embeddings.embed_documents(texts)

    print(f"Embeddings returned: {len(vectors)}")
    print(f"Dimensions per embedding: {len(vectors[0])}")

    assert len(vectors) == len(texts)
    assert all(len(vector) == 1536 for vector in vectors)

    print("PASS: OpenAI embeddings are working through LangChain")


if __name__ == "__main__":
    main()