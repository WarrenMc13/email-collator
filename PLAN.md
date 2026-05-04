# PropFlow CRM — Build Plan

Evolving the Property24 Email Collator CLI into a full-stack, multi-tenant property CRM SaaS.

---

## Overview

| Layer | Stack |
|---|---|
| Backend | FastAPI + SQLAlchemy 2 (async) + PostgreSQL + Celery + Redis |
| Frontend | React 18 + Vite + shadcn/ui + TanStack Query + React Router |
| Auth | JWT (access + refresh) with per-tenant role model |
| Email sync | Existing IMAP collator promoted to a background service |
| Infra | Docker Compose (app, postgres, redis, minio) |

---

## Versioned Milestones

### v0.1 — Foundation (current sprint)

**Module 1: Core Platform**
- [x] Project scaffold: `backend/`, `frontend/`, `backend/collator/`
- [x] FastAPI app factory with CORS, exception handlers, versioned router
- [x] SQLAlchemy async engine + `Base` + `get_db` dependency
- [x] Settings via `pydantic-settings` (`.env` driven)
- [ ] Alembic migration environment wired to async engine
- [ ] `Tenant`, `User`, `AuditLog`, `APIKey` models
- [ ] JWT auth: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`
- [ ] Per-tenant RBAC middleware (owner / admin / agent / viewer)

**Module 2: Lead Capture & Collation**
- [x] `MailboxConfig` + `SyncRun` models
- [ ] `MailboxConfig` CRUD router (create / list / update / delete / test-connection)
- [ ] Fernet encryption of stored IMAP passwords
- [ ] Celery worker + beat schedule for periodic sync
- [ ] Email sync service: wraps existing collator, upserts leads into DB
- [ ] `Lead`, `Contact`, `PipelineColumn` models

---

### v0.2 — Pipeline & Properties

**Module 3: Lead Pipeline**
- [ ] `Lead` CRUD router with filtering (status, source, assigned agent, date range)
- [ ] Pipeline column management (Kanban columns per tenant)
- [ ] Drag-and-drop stage update endpoint (`PATCH /leads/{id}/stage`)
- [ ] `Note` and `CallLog` models + endpoints
- [ ] Lead assignment endpoint

**Module 4: Property & Mandate Management**
- [ ] `Property`, `PropertyPhoto`, `Mandate` models
- [ ] Property CRUD + photo upload (MinIO/S3)
- [ ] Mandate creation (sale / rental) linked to property + agent
- [ ] `PortalSync` records (track which portals a listing is on)

---

### v0.3 — Deals & Offers

**Module 5: Offer & Deal Tracking**
- [ ] `Offer`, `Deal`, `DealMilestone`, `Commission` models
- [ ] Offer submit / accept / reject / counter workflow
- [ ] Deal milestone checklist (suspensive conditions, transfer date, etc.)
- [ ] Commission split calculator

---

### v0.4 — Rentals

**Module 6: Rental Management**
- [ ] `TenantApplication`, `Lease`, `RentPayment`, `MaintenanceRequest`, `Inspection` models
- [ ] Application → approval → lease workflow
- [ ] Rent payment recording + arrears flag
- [ ] Maintenance request lifecycle (open → assigned → resolved)
- [ ] Inspection scheduling + report upload

---

### v0.5 — Communications

**Module 7: Omni-channel Comms**
- [ ] `Message`, `EmailTemplate`, `NurtureSequence`, `NurtureStep` models
- [ ] SendGrid email dispatch
- [ ] WhatsApp Business API integration
- [ ] BulkSMS South Africa integration
- [ ] Nurture sequence engine (Celery beat, drip logic)

---

### v0.6 — Documents & e-Signatures

**Module 8: Document Management**
- [ ] `Document`, `ESignatureEnvelope` models
- [ ] File upload to MinIO (presigned URL pattern)
- [ ] DocuSign envelope create / send / webhook status update

---

### v0.7 — Compliance

**Module 9: FICA & POPIA**
- [ ] `FICAChecklist`, `FICADocument`, `FFCRecord`, `POPIAConsent` models
- [ ] FICA document checklist per contact (ID, POA, source of funds)
- [ ] FFC (Fidelity Fund Certificate) expiry tracking per agent
- [ ] POPIA consent capture + data deletion request workflow

---

### v0.8 — Financial

**Module 10: Trust Accounting & Invoicing**
- [ ] `TrustAccountEntry`, `Invoice` models
- [ ] Deposit / withdrawal journal (trust account ledger)
- [ ] Invoice generation (PDF) + Stripe payment link

---

### v0.9 — Reporting & Analytics

- [ ] Dashboard KPIs endpoint (leads per source, conversion rates, pipeline value)
- [ ] Agent performance report
- [ ] Monthly revenue + commission summary
- [ ] CSV / Excel export for any list view

---

### v1.0 — Billing & Multi-tenancy

- [ ] Stripe subscription management (starter / professional / enterprise plans)
- [ ] Usage metering (seats, storage, emails sent)
- [ ] Tenant onboarding wizard
- [ ] Subdomain routing per tenant

---

## Frontend Pages (React)

| Route | Component | v |
|---|---|---|
| `/login` | Auth forms | 0.1 |
| `/dashboard` | KPI cards + activity feed | 0.1 |
| `/leads` | Kanban board (drag-and-drop) | 0.2 |
| `/leads/:id` | Lead detail + timeline | 0.2 |
| `/properties` | Property grid | 0.2 |
| `/properties/:id` | Property detail + photos + mandates | 0.2 |
| `/deals` | Deal pipeline | 0.3 |
| `/rentals` | Tenancy list | 0.4 |
| `/comms` | Inbox + compose | 0.5 |
| `/documents` | Document library | 0.6 |
| `/compliance` | FICA / FFC status | 0.7 |
| `/finance` | Trust ledger + invoices | 0.8 |
| `/reports` | Analytics charts | 0.9 |
| `/settings` | Mailboxes, users, billing | 0.1 |

---

## Directory Layout

```
email-collator/
├── backend/
│   ├── app/
│   │   ├── config.py          # pydantic-settings
│   │   ├── database.py        # async engine + session
│   │   ├── main.py            # FastAPI factory
│   │   ├── auth.py            # JWT helpers + deps
│   │   ├── models/            # SQLAlchemy models (one file per domain)
│   │   ├── routers/           # FastAPI routers (one file per domain)
│   │   └── services/          # business logic
│   ├── collator/              # promoted from root CLI
│   │   ├── imap_client.py
│   │   ├── parser.py
│   │   └── output.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── lib/               # API client, auth store
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── PLAN.md
```

---

## Current Build Status

- [x] CLI collator works end-to-end (IMAP → parse → XLSX/CSV/HTML)
- [x] Backend scaffold created (`backend/app/`, `backend/collator/`)
- [x] `config.py`, `database.py`, `MailboxConfig`, `SyncRun`, `Tenant`, `User`, `AuditLog`, `APIKey` models written
- [ ] Alembic + remaining models
- [ ] Auth endpoints
- [ ] Frontend scaffold
