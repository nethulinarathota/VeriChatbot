# PROMPTS.md — Prompt Engineering Decisions

This document explains the system prompt design, classification strategy, and key decisions made in building the Veri chatbot.

---

## 1. Persona & System Prompt

**Persona name:** Veri

**System prompt (used for Verite-topic answers):**

```
You are Veri, a knowledgeable and professional research assistant for Verite Research.
Verite Research is a non-profit organisation that studies forced labour, human trafficking,
supply chain audits, responsible sourcing, and labour rights issues globally.

Your job:
- Answer questions using ONLY the context excerpts provided below.
- Be accurate, clear, and concise. Do not speculate beyond what the documents say.
- Always mention which publication your answer is drawn from.
- If the context doesn't fully answer the question, say so honestly.
- Never make up facts or cite sources not present in the context.
- Maintain a helpful, professional, and empathetic tone given the serious nature of the topics.
```

**Why these choices?**

- **"Answer using ONLY the context excerpts"** — prevents hallucination. Without this constraint, LLMs often blend retrieved content with general training knowledge, which could produce inaccurate citations.
- **"Mention which publication"** — enforces the citation requirement at the prompt level, not just the UI level.
- **"If the context doesn't fully answer, say so honestly"** — RAG systems fail silently when retrieval misses. Honest uncertainty is better than a confident wrong answer.
- **Empathetic tone instruction** — Verite's topics (forced labour, trafficking) are serious and sometimes emotionally charged. The model should not be flippant.

---

## 2. Message Classification

Before generating an answer, every user message is classified into one of three categories using a separate lightweight LLM call:

| Category | What it means | What the bot does |
|---|---|---|
| `greeting` | Small talk, hello, thanks | Responds warmly, no vector search |
| `verite` | Related to Verite's topics | Full RAG pipeline |
| `off_topic` | Unrelated (sports, cooking, etc.) | Politely declines |

**Why a separate classification call?**

Embedding every message and checking similarity to the knowledge base would misclassify "Hi!" as relevant if the corpus happens to contain the word "hi" somewhere. A small, cheap LLM call with explicit rules is more reliable for intent detection.

**Temperature = 0 for classification** — we want deterministic, reproducible classification, not creative variation.

---

## 3. Handling Borderline Questions

> *"What is forced labour?"* — a general definition question, not specifically about Verite's publications.

**Decision: Classify as `verite` and answer from context.**

**Rationale:**

Forced labour is the central research topic of Verite's work. A user asking "What is forced labour?" is almost certainly asking in the context of understanding Verite's publications, not looking for a Wikipedia definition. Rejecting this question would be unhelpful and confusing.

More broadly, our rule is: **if a topic is directly within Verite's domain of expertise, answer it — even if the question is phrased generally.** We'd rather answer one extra borderline question than leave a genuine researcher without help.

The classification prompt explicitly encodes this:
> *"including general questions on these topics even if not explicitly about Verite"*

**Counter-example:** "What is GDP?" — general economics, not Verite's field → `off_topic`.

---

## 4. Conversation History

The last 6 conversation turns are included in every Groq API call so follow-up questions like "Can you say more about that?" work correctly.

We cap at 6 turns to avoid exceeding the model's context window when conversations get long.

---

## 5. Chunking Strategy

- **Chunk size:** 600 characters
- **Overlap:** 100 characters

**Why 600 characters?** Long enough to contain a coherent paragraph with full context, short enough that retrieval returns precise passages rather than large walls of text.

**Why overlap?** If a key sentence falls at the boundary between two chunks, the 100-character overlap ensures it appears fully in at least one chunk. Without overlap, boundary sentences get split and lose meaning.

---

## 6. Retrieval (RAG)

- **Embedding model:** `all-MiniLM-L6-v2` (runs locally, no API cost, fast)
- **Top-k retrieved:** 4 chunks per query
- **Vector DB:** ChromaDB (persistent on disk — no re-embedding on restart)

The top 4 chunks are concatenated with their source metadata and injected into the LLM prompt as `CONTEXT`. The LLM is instructed to answer only from this context.

---

## 7. Sample Questions & Answers

| # | Question | Answer summary | Citation |
|---|---|---|---|
| 1 | What gaps does Verite identify in Sri Lanka's anti-corruption laws? | Describes missing provisions for private sector bribery, weak enforcement mechanisms, and comparison to international standards. | Gaps in the Guardrails (2025) |
| 2 | What does the State of the Budget 2026 say about government revenue? | Summarises revenue projections, tax policy changes, and fiscal targets from the report. | State of the Budget 2026 (2026) |
| 3 | Can you say more about that? (follow-up) | Expands on previous answer using conversation history — no new vector search needed. | Same source |
| 4 | What job search methods work best for unemployed youth in Sri Lanka? | Explains findings on social contacts vs. formal methods, and which are most effective. | Ineffectiveness of Social Contacts (2020) |
| 5 | Who is Virat Kohli? | Politely declined: "That's a bit outside my area!" | — |

---

## 8. Publications Used

| Title | Year | URL |
|---|---|---|
| Gaps in the Guardrails: A Review of Laws on Private Sector Corruption in Sri Lanka | 2025 | https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails_A_Review_of_Laws_on_Private_Sector_Corruption_in_Sri_Lanka.pdf |
| State of the Budget 2026 | 2026 | https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf |
| Ineffectiveness of Social Contacts and Alternate Job Search Methods for Unemployed Youth in Sri Lanka | 2020 | https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts-for-Unemployed-Youth-Working-Paper_June-2020-01.pdf |