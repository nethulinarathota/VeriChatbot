# PROMPTS.md - Prompt Engineering Decisions

This file documents how prompts and routing are designed in the current chatbot implementation.

## 1. Persona

Persona name: `Veri`

Core role:
- Professional research assistant for Verite Research
- Answers from provided document context
- Avoids speculation
- Cites publication source

## 2. Message Routing

The app classifies each input into:
- `greeting`: small talk/thanks; no retrieval
- `verite`: in-domain content; full RAG flow
- `off_topic`: polite decline

Guardrails added in code:
- If a publication filter is selected, treat query as in-domain
- If query is a summary-style request, treat query as in-domain

This prevents false off-topic responses for valid "summary of selected document" queries.

## 3. Borderline Question Policy

Example: "What is forced labour?"

Decision: classify as `verite` when topic is clearly within Verite's domain.

Rationale:
- The user intent is likely research-context understanding
- Rejecting such queries harms usefulness

Counter-example:
- "Who is Virat Kohli?" -> `off_topic`

## 4. Retrieval Strategy

Current retrieval is hybrid:
- Dense vector retrieval from FAISS
- Keyword retrieval from BM25
- Reciprocal rank fusion (RRF)

Publication filter:
- Sidebar selection can constrain retrieval to one publication

Summary-intent fallback:
- Broad summary prompts can have low per-chunk similarity
- If strict threshold filtering yields nothing, fallback keeps top filtered candidates

## 5. Query Rewriting

Follow-up queries are rewritten into standalone queries using the LLM.

If summary intent + selected publication:
- Rewrite is anchored with selected publication title to improve retrieval precision.

## 6. Chunking

Current values from code:
- Parent chunk size: `1200`
- Child chunk size: `400`
- Overlap: `80` (child overlap uses half)

Why parent/child:
- Child chunks improve retrieval granularity
- Parent chunks improve final answer coherence

## 7. Generation Prompt Behavior

System prompt enforces:
- Use only provided context
- No fabricated facts/sources
- Mention publication source
- Admit uncertainty when context is insufficient

## 8. Citation & Relevance

Returned answer includes:
- Citation: `Title (Year) - p.<page>`
- Relevance score shown in UI (aggregated from top retrieved chunks)

## 9. Required Behavior Coverage

- Greeting/small talk: no vector search
- Verite-content questions: retrieval + grounded answer + citation
- Follow-up questions: history-aware rewrite
- Out-of-scope questions: polite decline

## 10. Publications Used

1. Gaps in the Guardrails: A Review of Laws on Private Sector Corruption in Sri Lanka (2025)
   - https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails_A_Review_of_Laws_on_Private_Sector_Corruption_in_Sri_Lanka.pdf
2. State of the Budget 2026 (2026)
   - https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf
3. Ineffectiveness of Social Contacts and Alternate Job Search Methods for Unemployed Youth in Sri Lanka (2020)
   - https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts-for-Unemployed-Youth-Working-Paper_June-2020-01.pdf
