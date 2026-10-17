# Hakiki Dashboard — Setup

Refine + Ant Design + Vite. It has a login page, a **claim checker with a Glass Box trace**, and a **claims history** list.

## 1. Scaffold

```bash
cd hakiki-claims
npm create refine-app@latest dashboard
# Choose: Vite · REST API (simple-rest) · Ant Design · no example pages · no auth example
cd dashboard
npm install axios dayjs
cp .env.example .env
```

Copy the `src/` files from this folder over the scaffold's files.

> The imports target Refine v5 (`@refinedev/react-router`, `ThemedLayout`). If your scaffold generated v4 instead (`@refinedev/react-router-v6`, `ThemedLayoutV2`), keep the scaffold's imports and change only the providers, resources and routes.

## 2. Files

```
dashboard/
├── .env.example
└── src/
    ├── App.tsx                    # providers, resources, routes
    ├── types.ts                   # API contract (matches README §5.3)
    ├── lib/http.ts                # axios instance, cookie auth
    ├── providers/authProvider.ts  # login / logout / session check
    ├── components/TraceTree.tsx   # Glass Box trace + verdict tag
    └── pages/
        ├── check/index.tsx        # claim form → verdict, fixes, trace
        └── claims/list.tsx        # history table
```

## 3. Run

```bash
npm run dev          # http://localhost:5173
```

## 4. What the backend must provide

| Endpoint | Purpose |
|---|---|
| `POST /v1/auth/login` | Sets an **httpOnly, Secure, SameSite=Strict** session cookie |
| `POST /v1/auth/logout` | Clears the cookie |
| `GET /v1/auth/me` | 200 with `{ id, name, facility }`, or 401 |
| `POST /v1/claims/check` | Returns `CheckResult` (see `src/types.ts`) |
| `GET /v1/claims?_start&_end&_sort&_order` | List, with an `X-Total-Count` header |

FastAPI CORS must allow credentials and expose the count header:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # exact origins only, never "*" with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Total-Count"],
)
```

## 5. Security choices

- **No tokens in localStorage.** The session lives in an httpOnly cookie, so XSS can't steal it.
- **SameSite=Strict** on the cookie blocks CSRF for the hackathon. Add a CSRF token before cross-site deployments.
- All API text is rendered as React text, and `dangerouslySetInnerHTML` is never used, so malicious claim notes can't inject HTML.
- The form sends only the fields the rules need, with no patient names (data minimisation).
