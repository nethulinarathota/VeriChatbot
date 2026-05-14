# Veri — Verite Research Chatbot

A RAG-based AI chatbot that answers questions about Verite Research publications, built with Python, Streamlit, ChromaDB, and the Groq API.

---

## How It Works

```
User question
     │
     ▼
┌─────────────────────┐
│  Message Classifier  │  (Groq LLM, temp=0)
│  greeting / verite / │
│  off_topic           │
└─────────────────────┘
     │
     ├── greeting  → Friendly response, no DB search
     ├── off_topic → Polite decline
     └── verite    ──────────────────────────────────┐
                                                     ▼
                                         ┌─────────────────────┐
                                         │  Embed user query   │
                                         │  (all-MiniLM-L6-v2) │
                                         └─────────────────────┘
                                                     │
                                                     ▼
                                         ┌─────────────────────┐
                                         │  ChromaDB vector    │
                                         │  similarity search  │
                                         │  → top 4 chunks     │
                                         └─────────────────────┘
                                                     │
                                                     ▼
                                         ┌─────────────────────┐
                                         │  Groq LLM (llama-   │
                                         │  3.3-70b-versatile) │
                                         │  + conversation     │
                                         │  history            │
                                         └─────────────────────┘
                                                     │
                                                     ▼
                                         Answer + Citation tag
```

---

## Project Structure

```
verite-chatbot/
├── app.py          # Streamlit UI
├── chatbot.py      # RAG pipeline (PDF loading, ChromaDB, Groq)
├── PROMPTS.md      # Prompt engineering decisions
├── requirements.txt
├── .env.example
├── docs/           # Place your 3 Verite PDFs here (not committed)
│   ├── verite_forced_labour_recruitment.pdf
│   ├── verite_audit_failures.pdf
│   └── verite_responsible_sourcing.pdf
└── .chroma_store/  # Auto-created by ChromaDB (not committed)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/verite-chatbot.git
cd verite-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

```bash
cp .env.example .env
# Open .env and paste your Groq API key
```

### 5. Add the PDFs

Download the 3 publications from [Verite Research](https://www.veriteresearch.org/services-and-products/research-outputs/) and place them in the `docs/` folder with these exact filenames:

```
docs/verite_forced_labour_recruitment.pdf
docs/verite_audit_failures.pdf
docs/verite_responsible_sourcing.pdf
```

> Update `PUBLICATIONS` in `chatbot.py` if you choose different publications.

### 6. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Publications Used

| Title | Year | URL |
|---|---|---|
| Gaps in the Guardrails: A Review of Laws on Private Sector Corruption in Sri Lanka | 2025 | https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails... |
| State of the Budget 2026 | 2026 | https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf |
| Ineffectiveness of Social Contacts and Alternate Job Search Methods for Unemployed Youth in Sri Lanka | 2020 | https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts... |

---

## Sample Questions

| Question | What happens |
|---|---|
| "Hi!" | Veri greets you and introduces herself |
| "What gaps exist in Sri Lanka's anti-corruption laws?" | RAG answer with citation |
| "Can you say more about that?" | Follow-up using conversation history |
| "What does the 2026 budget say about revenue?" | RAG answer with citation |
| "Who is Virat Kohli?" | Politely declined |

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (get one at console.groq.com) |

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| UI | Streamlit | Pure Python, no JavaScript needed |
| LLM | Groq `llama-3.3-70b-versatile` | Fast inference, strong instruction-following |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Free, runs locally, good quality |
| Vector DB | ChromaDB | Easy setup, persists to disk |
| PDF parsing | pypdf | Lightweight, Python-native |