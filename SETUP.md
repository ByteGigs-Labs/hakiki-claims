# Hakiki Dashboard

Refine (headless) + React + Vite + TypeScript, with a custom design system in `dashboard/src/styles/` and no UI kit. Fonts are bundled through `@fontsource`, so nothing loads from a third-party host.

## Run

```bash
cd dashboard
cp .env.example .env     # VITE_API_URL, default http://localhost:8000
npm install
npm run dev              # http://localhost:5173
npm test                 # unit and component tests
npm run build            # type-check and production build
```

The API must allow the dashboard origin in `CORS_ORIGINS` and be running on `VITE_API_URL`.

## Layout

```
dashboard/src/
├── App.tsx                    # providers, resources, lazy routes
├── types.ts                   # API contract
├── lib/                       # http client, typed API calls, form logic, formatting
├── hooks/                     # useAsync, useCountUp
├── providers/authProvider.ts  # session cookie login, logout, identity
├── layout/Shell.tsx           # navigation rail
├── components/                # verdict, trace, fixes, gauge, drawers, dropzone
├── pages/                     # login, check, batch, claims history
└── styles/                    # tokens, base, shared components
```

## Security choices

- No tokens in `localStorage`. The session lives in an httpOnly, SameSite=Strict cookie set by the API.
- Every API string renders as a React text node, and `dangerouslySetInnerHTML` is never used.
- The claim form sends the patient identifier once, over TLS, and the API hashes it on arrival.
- Uploads are checked for type and size on the client, and again on the server.
