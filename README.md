# TechKraft Candidate Dashboard

A recruitment dashboard where TechKraft reviewers score job candidates and admins see everything.

![Dashboard](docs\screenshots\1.png)
![cadidate details](docs\screenshots\2.png)
![login](docs\screenshots\3.png)
## Quick Start

```bash
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/health

### Demo Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@techkraft.com | admin123 | Admin |
| reviewer1@techkraft.com | reviewer123 | Reviewer |
| reviewer2@techkraft.com | reviewer123 | Reviewer |

---

## Example curl Commands

```bash
# Register a new user (always gets "reviewer" role)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "new@example.com", "password": "mypassword"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "reviewer1@techkraft.com", "password": "reviewer123"}'

# List candidates (with token from login response)
curl http://localhost:8000/candidates \
  -H "Authorization: Bearer <TOKEN>"

# Filter candidates by status
curl "http://localhost:8000/candidates?status=reviewing" \
  -H "Authorization: Bearer <TOKEN>"

# Get single candidate
curl http://localhost:8000/candidates/1 \
  -H "Authorization: Bearer <TOKEN>"

# Submit a score
curl -X POST http://localhost:8000/candidates/1/scores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"category": "technical", "score": 4, "note": "Strong fundamentals"}'

# Generate AI summary (takes ~2 seconds)
curl -X POST http://localhost:8000/candidates/1/summary \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Architecture Decision Records (ADR)

### ADR-1: SQLite over PostgreSQL

**Context:** The project needs a relational database. PostgreSQL is the production standard, but adds Docker complexity and setup friction for a take-home.

**Decision:** Use SQLite with WAL mode and foreign keys enabled via PRAGMA.

**Trade-off:** No concurrent write scaling, no advanced JSON operators. Acceptable for a demo with single-digit concurrent users. Migration to PostgreSQL requires only changing the connection string and removing `check_same_thread`.

---

### ADR-2: Soft Delete via `deleted_at` Column

**Context:** Candidates should never be permanently deleted — compliance and audit trail requirements.

**Decision:** Add a nullable `deleted_at` timestamp column. All queries filter `WHERE deleted_at IS NULL`. No hard delete endpoint exists.

**Trade-off:** Slightly more complex queries (every read must filter). Gains: full audit trail, easy "undo", no data loss. The index on `status` still works because archived candidates can be filtered by status too.

---

### ADR-3: JWT Stored in localStorage

**Context:** Need stateless auth that works across page refreshes without a backend session store.

**Decision:** Store JWT in localStorage, send via `Authorization: Bearer` header.

**Trade-off:** Vulnerable to XSS (if an attacker injects script, they can read the token). Mitigated by: no `dangerouslySetInnerHTML`, no user-generated HTML rendering, short token expiry (60 min). For production, httpOnly cookies with CSRF protection would be stronger.

---

## Debugging Snippet

```python
# from a hypothetical service layer — what's wrong here?
def search_candidates(status: str, keyword: str, page: int, page_size: int):
    all_candidates = db.execute("SELECT * FROM candidates").fetchall()
    filtered = [c for c in all_candidates if c["status"] == status]
    # ... also filter by keyword in Python ...
    offset = (page - 1) * page_size
    return filtered[offset : offset + page_size]
```

**The Bug:** This function fetches the *entire* `candidates` table into Python memory, then applies filtering and pagination in application code instead of using SQL `WHERE` + `LIMIT/OFFSET`.

**Why It Matters at Scale:** With 100k+ candidates, every single request loads all rows into memory, applies O(n) filtering in Python, and discards most of the data. Memory usage grows linearly with table size regardless of how many results the user actually needs. The database's query optimizer, indexes (like the ones on `candidates.status` and `candidates.role_applied`), and built-in pagination capabilities are completely bypassed. Under concurrent load, this pattern causes memory spikes and GC pressure that degrades the entire service.

**The Correct Approach:** Push filtering and pagination into the SQL query itself — use `WHERE` clauses for status/keyword filtering and `LIMIT/OFFSET` for pagination. This lets the database use indexes and only transfer the rows you actually need over the wire.

**How This Project Does It Correctly:**

```python
# From app/services/candidate_service.py — filtering and pagination in SQL
query = db.query(Candidate).filter(Candidate.deleted_at.is_(None))

if status:
    query = query.filter(Candidate.status == status)
if keyword:
    query = query.filter(
        (Candidate.name.ilike(f"%{keyword}%"))
        | (Candidate.email.ilike(f"%{keyword}%"))
    )

total = query.count()
items = (
    query.order_by(Candidate.created_at.desc())
    .offset((page - 1) * page_size)
    .limit(page_size)
    .all()
)
```

SQLAlchemy's query builder compiles this into a single SQL statement with `WHERE`, `ORDER BY`, `LIMIT`, and `OFFSET` — the database does the heavy lifting using its indexes, and only the requested page of results is transferred to the application.

---

## Learning Reflection

The hardest problem I hit was the `passlib` + `bcrypt` version incompatibility inside Docker. Locally, tests passed because my system had an older bcrypt. Inside the container, pip pulled bcrypt 4.2 which removed the `__about__` attribute that passlib introspects at import time. The container crashed on startup with a cryptic `AttributeError` deep in passlib's backend loader — no stack frame pointed at my code.

I first tried upgrading passlib (no new release exists), then tried switching to argon2 (would break existing hashed passwords in the seed). What actually worked was pinning `bcrypt==4.0.1` — the last version with the old API surface. The lesson: when two libraries couple on internal implementation details rather than public APIs, version pinning isn't optional, it's load-bearing. I now pin all security-critical dependencies to exact versions and test the Docker build as part of CI, not as an afterthought.

---

## Limitations & Future Work

**Known Limitations:**

- No rate limiting on auth endpoints — brute-force protection would need middleware or a reverse proxy in production
- No refresh token flow — JWT expires after 60 minutes with no graceful renewal, user must re-login
- No frontend test coverage — component tests with Vitest + React Testing Library would be the next priority
- The SSE streaming endpoint (stretch goal) is not implemented
- No real LLM integration — the summary endpoint is a mock with a sleep delay
- SQLite doesn't support concurrent writes — fine for a demo, would need PostgreSQL for multi-user production use

**Given More Time:**

- Add WebSocket or SSE-based live score updates so reviewers see each other's scores appear in real time
- Add a proper admin panel for managing candidate status transitions (new → reviewing → interviewed → offered/rejected)
- Implement cursor-based pagination instead of offset-based for better performance on large datasets
- Add OpenTelemetry tracing to understand request latency across the service layer

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, python-jose (JWT), passlib (bcrypt)
- **Frontend:** React 18, Vite, React Router v6
- **Infrastructure:** Docker Compose
- **Design System:** Custom tokens based on Sentri design language (Space Grotesk + Rubik, violet/lime palette)
"# techkraft-candidate-dash" 
