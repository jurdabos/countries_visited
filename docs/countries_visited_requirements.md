# Countries Visited - Requirements Specification

*Version 0.1 - June 12 2025*

---

## 1  Introduction

The **Countries Visited** application allows individuals and small groups to record the countries they have visited, visualise them on an interactive world map and compare overlap statistics. This document captures the functional and non-functional requirements for the first public release, covering both local execution and deployment to **Streamlit Cloud**.

### 1.1  Purpose

- Provide a single authoritative reference for developers, testers, and stakeholders.
- Establish the agreed scope, behaviour, data model and technology stack, with mandatory and optional components clearly separated.

### 1.2  Stakeholders

| Role          | Interest                                                   |
|---------------|------------------------------------------------------------|
| Product owner | Overall vision and feature prioritisation                  |
| End users     | Accurate country records, easy-to-use map, shareable links |
| Developers    | Clear requirements, modern but lightweight tech stack      |
| Test/QA       | Comprehensive test coverage and predictable behaviour      |
| Operations    | Smooth deployment to Streamlit Cloud, monitoring           |

---

## 2  Scope

| In Scope                                        | Out of Scope                                   |
|-------------------------------------------------|------------------------------------------------|
| Single & multi-player visited-country tracking  | Real-time collaborative editing                |
| World map visualisation & per-player statistics | City/region-level granularity                  |
| Local HDF5 file storage                         | Alternative on-prem or container orchestration |
| OAuth sign-in (Google, GitHub)                  | Payments, internal user management             |
| Cloud deployment via Streamlit Cloud            | Deep mobile-native app                         |

---

## 3  Definitions & Acronyms

| Term               | Meaning                                                           |
|--------------------|-------------------------------------------------------------------|
| ISO-3166-1 alpha-2 | Two-letter country codes (e.g. **ES**, **US**)                    |
| HDF5               | Hierarchical Data Format v5, binary container for structured data |
| OAuth              | Open standard for delegate authorisation                          |
| Streamlit Cloud    | Fully managed hosting for Streamlit apps                          |

---

## 4  System Overview

The application is a **single-page Streamlit app (**\`\`**)** written in Python 3.9+. Locally, the user's data is stored in an **HDF5 file** in the working directory (default `countries.h5`). On Streamlit Cloud, the same code runs statelessly; users are encouraged to download/upload maps manually or configure an external persistent store.

---

## 5  Functional Requirements

### FR-1  Single-Player Mode

1. **Select mode** in sidebar.
2. Provide **search box** to filter countries by name or ISO code.
3. Enable **checkbox selection** of visited countries.
4. Display:
   - a coloured world map for the current player;
   - statistics (count, percentage, continent breakdown).

### FR-2  Multi-Player Mode

1. Sidebar toggle to **Multi Player**.
2. **Add new player** (name, colour – hex string validated against palette).
3. **Select player** to edit.
4. Record each player's visited countries independently.
5. Combined map layers distinguish players by colour.
6. **Overlap statistics** show countries visited by *all players* and *at least N players* (configurable).

### FR-3  Map Management

| Task             | Behaviour                                                                                 |
|------------------|-------------------------------------------------------------------------------------------|
| **New Map**      | Clears current in-memory state (*confirmation required*).                                 |
| **Download Map** | Saves current state to an HDF5 file and offers download (Streamlit file-download widget). |
| **Load Map**     | Upload widget accepts a valid HDF5 file; merges or replaces as per user choice.           |

### FR-4  Data Persistence

- Use **HDF5** for serialisation via *h5py* or *pandas.HDFStore*.
- Ensure schema compatibility with the structure in §7.
- Validate file integrity and version metadata on load.

### FR-5  Authentication (OAuth)

- Support optional sign-in with Google (initially) via OAuth 2.0.
- Store `access_token` only in session memory.
- On Streamlit Cloud, credentials are injected via **secrets** API.
- Redirect URI **must** match deployed app URL (e.g. `https://countries-visited.streamlit.app`).

### FR-6  Colour Palette Management (Optional)

- Load predefined palettes from `JSON\palettes.json`.
- Default palette applied when creating new players; custom hex overrides allowed.

---

## 6  Non-Functional Requirements

| ID                    | Requirement                                                                     |
|-----------------------|---------------------------------------------------------------------------------|
| NFR-1 Performance     | Map and statistics should update < 300 ms after user action on a modern laptop. |
| NFR-2 Usability       | UI follows Streamlit conventions; responsive layout down to 1024 px wide.       |
| NFR-3 Portability     | Runs on Windows, macOS, Linux with Python 3.9+.                                 |
| NFR-4 Reliability     | No data loss on local mode; graceful error when cloud session restarts.         |
| NFR-5 Security        | No secrets committed to Git; OAuth tokens stored server-side only.              |
| NFR-6 Maintainability | PEP 8-compliant code, typed with `typing`; CI checks pass.                      |
| NFR-7 Compliance      | Geographic data under CC-BY or public domain.                                   |

---

## 7  Data Models

### 7.1  User Authentication (Redis)

```
user:auth:<username>        (string)   # Stores hashed password
user:data:<username>        (string)   # JSON with user metadata
```

*Redis is used as a key-value store for fast user authentication and session management.*

### 7.2  Player Country Data (HDF5)

```
/                           (file root)
/metadata                   (group)
    ↳ version              (attr)   # e.g. "1.0"
/palettes                   (group)
    ↳ hex_codes            (1-D UTF-8 string dataset)
/players                    (group)
    ↳ <player-id>/         (subgroup per player)
           ↳ visited        (1-D UTF-8 string dataset)  # ISO codes
           ↳ colour         (attr)   # "#7ebce6"
           ↳ created        (attr)   # ISO-8601 timestamp
```

*All HDF5 datasets use gzip compression level 4.*

---

## 8  Technology Stack

| Layer                      | Mandatory                | Rationale                    | Optional / Future               |
|----------------------------|--------------------------|------------------------------|---------------------------------|
| Language                   | **Python 3.9 +**         | Broad library support        | –                               |
| Web UI                     | **Streamlit**            | Rapid, interactive data apps | –                               |
| User Auth Serialisation    | **Redis**                | Fast key-value store         | –                               |
| Player Data Serialisation  | **HDF5** via h5py        | Hierarchical, efficient      | Parquet export (arrow)          |
| DB (prod)                  | –                        | –                            | DuckDB or MySQL if multi-tenant |
| Workflow                   | –                        | –                            | Airflow for scheduled backups   |
| VCS                        | **git / GitHub**         | Required by Streamlit Cloud  | –                               |

*Less tech is preferred; optional items should not introduce extra dependencies for MVP.*

---

## 9  Deployment

### 9.1  Local Development

1. `git clone` repo, `cd countries_visited`.
2. `pip install -r requirements.txt`.
3. `streamlit run app.py`.
4. HDF5 file is created in working directory.

### 9.2  Streamlit Cloud

1. **Push** code to a public/private GitHub repo.
2. Log into **Streamlit Cloud** with GitHub.
3. **New App** → select repository/branch.
4. Configure runtime:
   - Main file: `app.py`
   - Python 3.9+
   - Secrets: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`.
5. Deploy.

#### 9.2.1  File-Storage Considerations

- Streamlit's ephemeral filesystem resets on each redeploy or idle shutdown.
- Recommend **persistent backend** for production: e.g. AWS S3, Google Cloud Storage or SQLite DB on Cloud SQL.
- Provide user-driven **Download/Upload Map** workflow as temporary workaround.

#### 9.2.2  OAuth Considerations

- Redirect URI **must** match cloud URL exactly.
- Renewal handled by Streamlit session state; logout deletes tokens.
- Rate limits and secrets rotation documented in `SECURITY.md`.

---

## 10  Testing Strategy

| Layer       | Tooling                       | Coverage Goal                   |
|-------------|-------------------------------|---------------------------------|
| Unit        | `pytest`, `unittest.mock`     | ≥ 90 % of core modules          |
| Integration | `pytest-asyncio`              | API boundaries (HDF5 ↔ UI)      |
| End-to-End  | `playwright` headless browser | Main user flows                 |
| CI          | GitHub Actions                | Lint, type-check, tests on push |

---

## 11  Assumptions & Constraints

- Single user per browser session; no simultaneous editing safeguards.
- Country list sourced from Natural Earth; updates unlikely to break codes.
- Streamlit Cloud free tier limits (memory, compute) are sufficient for MVP.

---

## 12  Open Issues / Future Enhancements

1. **Persistent Storage Interface** – pluggable backend (S3, DuckDB).
2. **Real-time Collaboration** – WebSocket sync across clients.
3. **Regional Detail** – add sub-national regions, cities.
4. **Mobile Optimisation** – responsive layout testing below 768 px.
5. **Analytics** – anonymous usage metrics to guide UX improvements.

---

*End of document*
