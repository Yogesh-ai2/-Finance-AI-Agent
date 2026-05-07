import os
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from langchain_ollama import OllamaEmbeddings

connections.connect(host="localhost", port="19532")

if utility.has_collection("fpna_reports"):
    utility.drop_collection("fpna_reports")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="report_name", dtype=DataType.VARCHAR, max_length=200),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
]

schema = CollectionSchema(fields=fields, description="FPNA reports")
col = Collection("fpna_reports", schema)
emb = OllamaEmbeddings(model="nomic-embed-text")

names, contents, vecs = [], [], []

for filename in os.listdir("data/reports"):
    if filename.endswith(".txt"):
        with open(os.path.join("data/reports", filename)) as f:
            text = f.read()
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for i, chunk in enumerate(chunks):
            vec = emb.embed_query(chunk)
            names.append(f"{filename}_chunk_{i}")
            contents.append(chunk)
            vecs.append(vec)
            print(f"done: {filename} chunk {i}")

col.insert([names, contents, vecs])
col.create_index("embedding", {"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}})
col.flush()
col.load()
print(f"total: {col.num_entities}")
