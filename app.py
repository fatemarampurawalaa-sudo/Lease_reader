import re, time
import numpy as np
import pandas as pd
import streamlit as st
import chromadb
from pypdf import PdfReader
from pydantic import BaseModel
from google import genai
from google.genai import types

CHAT_MODEL = "gemini-flash-lite-latest"
EMBED_MODEL = "gemini-embedding-001"
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


class LeaseDetails(BaseModel):
    tenant_name: str
    landlord_name: str
    property_address: str
    bedrooms: int
    furnished: bool
    annual_rent: int
    number_of_cheques: int
    start_date: str
    end_date: str
    security_deposit: int | None = None
    parking_space: str | None = None
    pets_allowed: bool
    renewal_notice_days: int | None = None


def read_pdf(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() for page in reader.pages)


def extract_lease(text):
    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=f"""Extract the lease details from this contract.
Dates must be in YYYY-MM-DD format. Amounts must be numbers in AED.
If a detail is not in the contract, leave it empty.

Contract:
{text}""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LeaseDetails,
        ),
    )
    return response.parsed.model_dump()


def chunk_by_section(text):
    parts = re.split(r"\n(?=\d+\.\s)", text)
    return [p.strip().replace("\n", " ") for p in parts if p.strip()]


def embed(text):
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return np.array(result.embeddings[0].values)


def ask_lease(question, collection, top_k=2):
    q_vector = embed(question)
    found = collection.query(query_embeddings=[q_vector.tolist()], n_results=top_k)
    context = "\n".join(f"[{i}] {d}" for i, d in zip(found["ids"][0], found["documents"][0]))
    prompt = f"""You answer questions about a tenancy contract.
Use ONLY the contract sections below.
If the answer is not in them, reply exactly: "I don't know, this is not in the contract."
Keep the answer to 1-2 sentences.
At the end write "Source:" and the [section id] you used, or "Source: none".

Contract sections:
{context}

Question: {question}"""
    response = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    return response.text


# ---------------- The web page ----------------
st.title("🏠 Lease Reader")
st.write("Upload a lease PDF to see its key details and ask questions about it.")
st.caption("Demo only – please upload sample leases, not real contracts.")

uploaded = st.file_uploader("Upload a lease PDF", type="pdf")

if uploaded:
    if st.session_state.get("file_name") != uploaded.name:
        with st.spinner("Reading the lease... (about 20 seconds)"):
            text = read_pdf(uploaded)
            st.session_state.details = extract_lease(text)

            chunks = chunk_by_section(text)
            vectors = []
            for c in chunks:
                vectors.append(embed(c))
                time.sleep(1)

            db = chromadb.Client()
            collection = db.create_collection(name=f"lease_{int(time.time())}")
            collection.add(
                ids=[f"section_{i}" for i in range(len(chunks))],
                documents=chunks,
                embeddings=[v.tolist() for v in vectors],
            )
            st.session_state.collection = collection
            st.session_state.file_name = uploaded.name

    st.subheader("📋 Lease details")
    rows = [(k.replace("_", " ").title(), str(v)) for k, v in st.session_state.details.items()]
    st.table(pd.DataFrame(rows, columns=["Detail", "Value"]))

    st.subheader("💬 Ask a question")
    question = st.text_input("For example: Is parking included?")
    if question:
        with st.spinner("Thinking..."):
            st.write(ask_lease(question, st.session_state.collection))
