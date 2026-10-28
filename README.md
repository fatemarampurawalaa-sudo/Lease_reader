# 🏠 Lease Reader – AI Contract Assistant

**🔗 Live demo:** https://kxhtqbyxayndg5wcvoadmg.streamlit.app

**📄 Try it with:** [sample_lease.pdf](sample_lease.pdf)

An AI tool that reads tenancy contracts (PDF), extracts the key details into a table, and answers questions about the lease with the exact section as source.

## The problem
Property companies manage hundreds of lease contracts. Finding the rent, dates, deposit or rules in each PDF by hand is slow and error-prone.

## What it does
1. **Extracts key details** – tenant, landlord, property, rent, cheques, start/end dates, deposit, parking, pets, renewal notice – into a structured table (ready for Excel, SQL or Power BI)
2. **Answers questions** about the lease in plain English, citing the contract section used
3. **Says "I don't know"** when the answer is not in the contract, instead of making things up

## How it works
1. **Read** – extract text from the PDF (pypdf)
2. **Extract** – Gemini returns the key details using a JSON schema (structured output)
3. **Store** – split the contract into sections, create embeddings, save in a vector database (ChromaDB)
4. **Answer** – for each question, retrieve the most relevant sections and let Gemini answer only from them, with the source (RAG)

## Testing
Evaluated with a test set of known answers:
- Extraction accuracy: 9 / 9 fields correct
- Q&A accuracy: 5 / 5, including an unanswerable question correctly answered with "I don't know"

## Tech stack
Python · Google Gemini API · Pydantic · ChromaDB · pypdf · pandas · Streamlit

## Note
Uses a sample (fictional) lease only. No real tenant data.

## Possible improvements
- OCR for scanned PDFs
- Process many leases at once and export to Excel / SQL
- Lease expiry alerts and a Power BI dashboard
