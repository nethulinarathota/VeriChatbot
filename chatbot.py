"""
chatbot.py — Verite Research Chatbot, full rebuild.

Improvements over v1:
  - FAISS vector search + BM25 keyword search (hybrid RRF fusion)
  - PDF upload via UI (add papers at runtime)
  - Parent-child chunking
  - Chunk deduplication
  - Query rewriting for follow-up questions
  - Faithfulness check (hallucination guard)
  - Similarity score threshold ("I don't know" guard)
  - Long-term memory across sessions (SQLite)
  - Suggested follow-up questions
  - Async knowledge base build (non-blocking)
  - Metadata filtering by publication
"""

import os
import re
import pickle
import sqlite3
import json
import math
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

DOCS_DIR     = Path("docs")
FAISS_DIR    = Path(".faiss_store")
FAISS_INDEX  = FAISS_DIR / "index.faiss"
FAISS_META   = FAISS_DIR / "metadata.pkl"
MEMORY_DB    = Path(".memory/memory.db")
GROQ_MODEL   = "llama-3.3-70b-versatile"

CHILD_CHUNK  = 400
PARENT_CHUNK = 1200
OVERLAP      = 80
TOP_K        = 8
FINAL_K      = 4
SIM_THRESHOLD = 0.25
HYBRID_ALPHA  = 0.6   # 1.0 = pure vector, 0.0 = pure BM25

BUILTIN_PUBS = [
    {
        "filename": "paper1.pdf",
        "title": "Gaps in the Guardrails: A Review of Laws on Private Sector Corruption in Sri Lanka",
        "year": "2025",
        "url": "https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails_A_Review_of_Laws_on_Private_Sector_Corruption_in_Sri_Lanka.pdf",
    },
    {
        "filename": "paper2.pdf",
        "title": "State of the Budget 2026",
        "year": "2026",
        "url": "https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf",
    },
    {
        "filename": "paper3.pdf",
        "title": "Ineffectiveness of Social Contacts and Alternate Job Search Methods for Unemployed Youth in Sri Lanka",
        "year": "2020",
        "url": "https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts-for-Unemployed-Youth-Working-Paper_June-2020-01.pdf",
    },
]


# ── BM25 ──────────────────────────────────────────────────────────────────────

class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b  = b
        self.corpus_size = 0
        self.avgdl       = 0
        self.idf         = {}
        self.doc_freqs   = []
        self.doc_len     = []

    def _tok(self, text):
        return re.findall(r'\w+', text.lower())

    def fit(self, corpus):
        tokenized        = [self._tok(d) for d in corpus]
        self.corpus_size = len(corpus)
        self.doc_len     = [len(t) for t in tokenized]
        self.avgdl       = sum(self.doc_len) / self.corpus_size if self.corpus_size else 1

        df = defaultdict(int)
        for tokens in tokenized:
            for w in set(tokens):
                df[w] += 1
        for w, f in df.items():
            self.idf[w] = math.log((self.corpus_size - f + 0.5) / (f + 0.5) + 1)

        self.doc_freqs = []
        for tokens in tokenized:
            freq = defaultdict(int)
            for t in tokens:
                freq[t] += 1
            self.doc_freqs.append(dict(freq))

    def get_scores(self, query):
        tokens = self._tok(query)
        scores = np.zeros(self.corpus_size)
        for w in tokens:
            if w not in self.idf:
                continue
            idf = self.idf[w]
            for i, freq in enumerate(self.doc_freqs):
                f  = freq.get(w, 0)
                dl = self.doc_len[i]
                scores[i] += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return scores


# ── Memory store (SQLite) ─────────────────────────────────────────────────────

class MemoryStore:
    def __init__(self):
        MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT, role TEXT, content TEXT,
                citation TEXT, timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE, title TEXT, year TEXT,
                url TEXT, added_at TEXT
            );
        """)
        self.conn.commit()

    def save_message(self, session_id, role, content, citation=None):
        self.conn.execute(
            "INSERT INTO conversations (session_id,role,content,citation,timestamp) VALUES (?,?,?,?,?)",
            (session_id, role, content, citation, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_history(self, session_id, limit=20):
        rows = self.conn.execute(
            "SELECT role,content,citation FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        return [{"role": r[0], "content": r[1], "citation": r[2]} for r in reversed(rows)]

    def get_all_sessions(self):
        rows = self.conn.execute(
            "SELECT session_id,MIN(timestamp),COUNT(*) FROM conversations GROUP BY session_id ORDER BY MIN(timestamp) DESC"
        ).fetchall()
        return [{"session_id": r[0], "started": r[1], "messages": r[2]} for r in rows]

    def save_publication(self, filename, title, year, url):
        self.conn.execute(
            "INSERT OR IGNORE INTO publications (filename,title,year,url,added_at) VALUES (?,?,?,?,?)",
            (filename, title, year, url, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_publications(self):
        rows = self.conn.execute("SELECT filename,title,year,url FROM publications").fetchall()
        return [{"filename": r[0], "title": r[1], "year": r[2], "url": r[3]} for r in rows]


# ── VeriteChatbot ─────────────────────────────────────────────────────────────

class VeriteChatbot:

    def __init__(self):
        self.groq    = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.dim     = 384
        self.memory  = MemoryStore()

        self.index      = None
        self.chunks     = []   # child texts
        self.parents    = []   # parent texts
        self.metadata   = []
        self.parent_idx = []
        self.bm25       = None
        self._lock      = threading.Lock()
        self._building  = False
        self._progress  = ""

        self._load_if_exists()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_if_exists(self):
        if FAISS_INDEX.exists() and FAISS_META.exists():
            self.index = faiss.read_index(str(FAISS_INDEX))
            with open(FAISS_META, "rb") as f:
                s = pickle.load(f)
            self.chunks     = s["chunks"]
            self.metadata   = s["metadata"]
            # "parents" and "parent_idx" were added in v2 — fall back gracefully
            # for index files built by the older single-chunk version.
            self.parents    = s.get("parents",    self.chunks)   # treat every child as its own parent
            self.parent_idx = s.get("parent_idx", list(range(len(self.chunks))))
            self._fit_bm25()
            print(f"[INFO] Loaded {len(self.chunks)} chunks from disk.")

    def _save(self):
        FAISS_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(FAISS_INDEX))
        with open(FAISS_META, "wb") as f:
            pickle.dump({"chunks": self.chunks, "parents": self.parents,
                         "metadata": self.metadata, "parent_idx": self.parent_idx}, f)

    def _fit_bm25(self):
        if self.chunks:
            self.bm25 = BM25()
            self.bm25.fit(self.chunks)

    # ── Build ─────────────────────────────────────────────────────────────────

    def build_knowledge_base(self):
        if self.index is not None and self.chunks:
            return
        self._ingest(BUILTIN_PUBS)
        for p in BUILTIN_PUBS:
            self.memory.save_publication(p["filename"], p["title"], p["year"], p["url"])

    def add_paper_async(self, pdf_bytes: bytes, title: str, year: str, url: str = "") -> str:
        fname    = f"upload_{hashlib.md5(pdf_bytes).hexdigest()[:8]}.pdf"
        pdf_path = DOCS_DIR / fname
        DOCS_DIR.mkdir(exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)
        pub = {"filename": fname, "title": title, "year": year, "url": url}
        self.memory.save_publication(fname, title, year, url)
        t = threading.Thread(target=self._add_blocking, args=(pub,), daemon=True)
        t.start()
        return fname

    def _add_blocking(self, pub):
        with self._lock:
            self._building = True
            self._progress = f"Indexing '{pub['title']}'…"
            try:
                self._ingest([pub])
            finally:
                self._building = False
                self._progress = ""

    def _ingest(self, pubs):
        new_children, new_parents, new_meta, new_pidx = [], [], [], []

        for pub in pubs:
            path = DOCS_DIR / pub["filename"]
            if not path.exists():
                print(f"[WARN] {path} not found, skipping.")
                continue

            pages         = self._read_pdf(path)
            parent_chunks = self._chunk(pages, pub, PARENT_CHUNK, OVERLAP)
            child_chunks  = self._chunk(pages, pub, CHILD_CHUNK,  OVERLAP // 2)

            base_parent_offset = len(self.parents) + len(new_parents)

            for child_text, child_meta in child_chunks:
                h = hashlib.md5(child_text.encode()).hexdigest()
                if any(hashlib.md5(c.encode()).hexdigest() == h for c in self.chunks + new_children):
                    continue
                best_pi, best_ov = 0, 0
                for pi, (pt, _) in enumerate(parent_chunks):
                    ov = len(set(child_text.split()) & set(pt.split()))
                    if ov > best_ov:
                        best_ov = ov
                        best_pi = base_parent_offset + pi
                new_children.append(child_text)
                new_meta.append(child_meta)
                new_pidx.append(best_pi)

            for pt, _ in parent_chunks:
                new_parents.append(pt)

        if not new_children:
            return

        emb = self.embedder.encode(new_children, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(emb)

        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dim)

        self.index.add(emb)
        self.chunks     += new_children
        self.parents    += new_parents
        self.metadata   += new_meta
        self.parent_idx += new_pidx
        self._fit_bm25()
        self._save()
        print(f"[INFO] Index: {len(self.chunks)} chunks total.")

    # ── PDF helpers ───────────────────────────────────────────────────────────

    def _read_pdf(self, path):
        reader = PdfReader(str(path))
        pages  = []
        for i, page in enumerate(reader.pages, 1):
            text = re.sub(r'\s+', ' ', page.extract_text() or "").strip()
            if text:
                pages.append({"page": i, "text": text})
        return pages

    def _chunk(self, pages, pub, size, overlap):
        out = []
        for p in pages:
            text, pnum = p["text"], p["page"]
            start = 0
            while start < len(text):
                c = text[start:start + size]
                if c.strip():
                    out.append((c, {
                        "source_title": pub["title"],
                        "source_year":  pub["year"],
                        "source_url":   pub.get("url", ""),
                        "source_file":  pub["filename"],
                        "page_number":  pnum,
                    }))
                start += size - overlap
        return out

    def _is_summary_query(self, text: str) -> bool:
        t = (text or "").lower()
        summary_terms = (
            "summary", "summarize", "summarise", "overview",
            "key findings", "main findings", "highlights",
            "this document", "this paper", "selected document",
        )
        return any(term in t for term in summary_terms)

    # ── Hybrid retrieve ───────────────────────────────────────────────────────

    def _retrieve(self, query, filter_title=None, user_input=None):
        if not self.chunks or self.index is None:
            return []

        qvec = self.embedder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(qvec)
        k = min(TOP_K * 3, self.index.ntotal)
        scores, indices = self.index.search(qvec, k)
        vec_s = {int(i): float(s) for i, s in zip(indices[0], scores[0]) if i != -1}

        bm25_raw  = self.bm25.get_scores(query) if self.bm25 else np.zeros(len(self.chunks))
        bm25_max  = bm25_raw.max() or 1
        bm25_norm = {i: float(bm25_raw[i]) / bm25_max for i in range(len(self.chunks))}

        vec_rank  = sorted(vec_s.keys(),   key=lambda i: vec_s.get(i, 0),   reverse=True)
        bm25_rank = sorted(bm25_norm.keys(), key=lambda i: bm25_norm.get(i, 0), reverse=True)

        rrf = defaultdict(float)
        for rank, i in enumerate(vec_rank):
            rrf[i] += HYBRID_ALPHA / (60 + rank + 1)
        for rank, i in enumerate(bm25_rank):
            rrf[i] += (1 - HYBRID_ALPHA) / (60 + rank + 1)

        sorted_ids = sorted(rrf.keys(), key=lambda i: rrf[i], reverse=True)
        is_summary = self._is_summary_query(user_input or query)

        if filter_title:
            sorted_ids = [i for i in sorted_ids if self.metadata[i].get("source_title") == filter_title]

        threshold_ids = [i for i in sorted_ids if vec_s.get(i, 0) >= SIM_THRESHOLD]
        # If a publication filter is explicitly selected, avoid hard-failing on strict
        # similarity thresholds for broad prompts like "summarize this paper".
        if threshold_ids:
            sorted_ids = threshold_ids
        elif filter_title:
            sorted_ids = sorted_ids[: max(FINAL_K * 2, 8)]
        elif is_summary:
            sorted_ids = sorted_ids[: max(FINAL_K * 2, 8)]
        else:
            sorted_ids = []

        seen, results = set(), []
        for i in sorted_ids:
            pidx = self.parent_idx[i]
            if pidx in seen:
                continue
            seen.add(pidx)
            m = self.metadata[i]
            results.append({
                "text":         self.parents[pidx],
                "source_title": m["source_title"],
                "source_year":  m["source_year"],
                "page_number":  m["page_number"],
                "source_url":   m.get("source_url", ""),
                "score":        vec_s.get(i, 0),
                "bm25_score":   bm25_norm.get(i, 0),
                "hybrid_rank":  rrf.get(i, 0),
            })
            if len(results) >= FINAL_K:
                break

        return results

    # ── Query rewrite ─────────────────────────────────────────────────────────

    def _rewrite(self, user_input, history, filter_title=None):
        if not history:
            q = user_input
        else:
            hist_str = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-4:])
            prompt = f"""Rewrite the follow-up as a standalone search query. Return ONLY the query.

History:
{hist_str}

Follow-up: {user_input}
Standalone query:"""
            r = self.groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80, temperature=0
            )
            q = r.choices[0].message.content.strip() or user_input

        if filter_title and self._is_summary_query(user_input):
            return f"{q} {filter_title} detailed summary key findings"
        return q

    # ── Classify ──────────────────────────────────────────────────────────────

    def _classify(self, text):
        prompt = f"""Classify for a Verite Research chatbot. Reply ONE word: greeting, verite, or off_topic.

Verite covers: Sri Lanka budget, anti-corruption law, private sector corruption, corporate governance, youth unemployment, job search, economic policy, forced labour, supply chains.

- greeting: small talk, hi, thanks
- verite: Verite topics (including general questions like "what is forced labour?")
- off_topic: sports, cooking, celebrities, unrelated tech, foreign politics

Message: "{text}"
Category:"""
        r = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5, temperature=0
        )
        c = r.choices[0].message.content.strip().lower()
        return c if c in ("greeting", "verite", "off_topic") else "verite"

    # ── Faithfulness ──────────────────────────────────────────────────────────

    def _faithfulness(self, answer, context):
        prompt = f"""Is this answer fully supported by the context? Reply JSON only: {{"faithful": true/false, "reason": "one sentence"}}

Context:
{context[:2000]}

Answer:
{answer}

JSON:"""
        r = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100, temperature=0
        )
        try:
            t = re.sub(r'```json|```', '', r.choices[0].message.content.strip()).strip()
            d = json.loads(t)
            return d.get("faithful", True), d.get("reason", "")
        except Exception:
            return True, ""

    # ── Follow-up suggestions ─────────────────────────────────────────────────

    def _suggest(self, question, answer):
        prompt = f"""Suggest 3 short follow-up questions a researcher might ask. Return a JSON array of strings only.

Q: {question}
A: {answer[:400]}

JSON:"""
        r = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150, temperature=0.5
        )
        try:
            t = re.sub(r'```json|```', '', r.choices[0].message.content.strip()).strip()
            s = json.loads(t)
            return s[:3] if isinstance(s, list) else []
        except Exception:
            return []

    # ── Main chat ─────────────────────────────────────────────────────────────

    def chat(self, user_input, history, session_id="default", filter_title=None):
        self.memory.save_message(session_id, "user", user_input)
        category = self._classify(user_input)
        # Guardrail: summary-style prompts should always route into retrieval.
        # Keep true off-topic declines active even when a publication filter is selected.
        if self._is_summary_query(user_input):
            category = "verite"

        if category == "greeting":
            prompt = f"""You are Veri, a friendly assistant for Verite Research. Respond warmly and briefly to this greeting. Mention you can help with their publications on Sri Lanka's budget, anti-corruption laws, and youth employment.
User: {user_input}"""
            r = self.groq.chat.completions.create(
                model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}],
                max_tokens=120, temperature=0.7
            )
            resp = r.choices[0].message.content.strip()
            self.memory.save_message(session_id, "assistant", resp)
            return {"response": resp, "citation": None, "suggestions": [],
                    "faithful": True, "score": 1.0, "rewritten_query": user_input}

        if category == "off_topic":
            resp = ("That's outside my area! I'm Veri, specialising in Verite Research's work on "
                    "Sri Lanka's budget, anti-corruption laws, and youth employment. Ask me anything on those topics!")
            self.memory.save_message(session_id, "assistant", resp)
            return {"response": resp, "citation": None, "suggestions": [],
                    "faithful": True, "score": 1.0, "rewritten_query": user_input}

        rewritten = self._rewrite(user_input, history, filter_title=filter_title)
        chunks    = self._retrieve(rewritten, filter_title=filter_title, user_input=user_input)

        if not chunks:
            resp = ("I couldn't find relevant information in the indexed publications. "
                    "Try rephrasing, or check that the relevant paper has been uploaded.")
            self.memory.save_message(session_id, "assistant", resp)
            return {"response": resp, "citation": None, "suggestions": [],
                    "faithful": True, "score": 0.0, "rewritten_query": rewritten}

        context_str = "\n\n---\n\n".join(
            f"[Source: {c['source_title']} ({c['source_year']}), Page {c['page_number']}]\n{c['text']}"
            for c in chunks
        )

        sys_prompt = """You are Veri, a professional research assistant for Verite Research — a Sri Lankan think tank covering public finance, budget analysis, anti-corruption legislation, private sector governance, youth employment, and economic policy.

Rules:
- Answer using ONLY the provided context excerpts.
- Be accurate, clear, and concise. Do not speculate.
- Always mention which publication your answer is drawn from.
- If the context doesn't fully answer the question, say so honestly.
- Never fabricate facts or sources."""

        messages = [{"role": "system", "content": sys_prompt}]
        for m in history[-6:]:
            if m["role"] in ("user", "assistant"):
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": f"CONTEXT:\n{context_str}\n\nQUESTION: {user_input}"})

        r = self.groq.chat.completions.create(
            model=GROQ_MODEL, messages=messages, max_tokens=700, temperature=0.3
        )
        answer = r.choices[0].message.content.strip()

        faithful, _ = self._faithfulness(answer, context_str)
        if not faithful:
            answer += "\n\n⚠️ *Parts of this answer may go beyond the source documents — please verify.*"

        suggestions = self._suggest(user_input, answer)

        top      = chunks[0]
        agg_vec  = float(np.mean([c["score"] for c in chunks[: min(3, len(chunks))]]))
        agg_bm25 = float(np.mean([c.get("bm25_score", 0.0) for c in chunks[: min(3, len(chunks))]]))
        ui_score = max(0.0, min(1.0, (0.7 * agg_vec) + (0.3 * agg_bm25)))
        citation = f"{top['source_title']} ({top['source_year']}) — p.{top['page_number']}"
        self.memory.save_message(session_id, "assistant", answer, citation)

        return {
            "response":        answer,
            "citation":        citation,
            "suggestions":     suggestions,
            "faithful":        faithful,
            "score":           ui_score,
            "source_excerpt":  top["text"],
            "rewritten_query": rewritten,
        }

    # ── Utilities ─────────────────────────────────────────────────────────────

    def get_chunk_count(self):
        return len(self.chunks)

    def get_publication_list(self):
        seen = []
        for m in self.metadata:
            t = m.get("source_title", "")
            if t and t not in seen:
                seen.append(t)
        return seen

    def is_building(self):
        return self._building

    def build_progress(self):
        return self._progress
