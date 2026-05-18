# Veri - Verite Research Chatbot

A Streamlit-based RAG chatbot for Verite Research publications.

## What It Does

- Loads 3 Verite PDFs from `docs/`
- Extracts text with `pypdf`
- Chunks into parent/child segments
- Embeds with `all-MiniLM-L6-v2`
- Retrieves with hybrid search (FAISS + BM25 RRF)
- Answers using Groq `llama-3.3-70b-versatile`
- Maintains in-session conversation history
- Stores long-term memory in SQLite
- Shows citation with publication + year + page

## Setup

1. Create and activate venv
2. Install deps: `pip install -r requirements.txt`
3. Create `.env` from `.env.example` and set `GROQ_API_KEY`
4. Place PDFs in `docs/` as:
   - `paper1.pdf`
   - `paper2.pdf`
   - `paper3.pdf`
5. Run: `streamlit run app.py`

## Publications Used

| Title | Year | URL |
|---|---|---|
| Gaps in the Guardrails: A Review of Laws on Private Sector Corruption in Sri Lanka | 2025 | https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails_A_Review_of_Laws_on_Private_Sector_Corruption_in_Sri_Lanka.pdf |
| State of the Budget 2026 | 2026 | https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf |
| Ineffectiveness of Social Contacts and Alternate Job Search Methods for Unemployed Youth in Sri Lanka | 2020 | https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts-for-Unemployed-Youth-Working-Paper_June-2020-01.pdf |

## Sample Questions and Answers

| Question | Chatbot answer (example) |
|---|---|
| Hi! | "Hi, I'm Veri. I can help with Verite Research publications on Sri Lanka's budget, anti-corruption laws, and youth employment." |
| What gaps exist in Sri Lanka's anti-corruption laws? | Summarises legal gaps in private sector corruption controls and cites *Gaps in the Guardrails (2025)* with page reference. |
| What does the State of the Budget 2026 say about government revenue? | Summarises revenue projections, tax policy directions, and fiscal implications, citing *State of the Budget 2026 (2026)*. |
| Can you say more about that? | Expands prior response using conversation history and keeps source grounding. |
| Who is Virat Kohli? | "That's outside my area..." polite decline and redirect to Verite topics. |

## Environment Variables

- `GROQ_API_KEY`: required

## Notes

- Retrieval is FAISS + BM25 (hybrid), not ChromaDB.
- Upload-from-UI is currently removed for assignment submission flow.
