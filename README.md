# StivaFresh

A work-in-progress grocery and expiry-tracking web application built by Shreya Tiwari.
Track freshness, store smarter, and reduce avoidable food waste.

## What it does

- Add, list and remove groceries, with records stored in SQLite.
- Track recorded expiry dates and show dashboard counts and items nearing their dates.
- Prioritise groceries in a Use First view.
- Suggest simple recipes by matching ingredient names to a built-in recipe list.
- Keep a shopping checklist in the browser's local storage.
- Provide rule-based storage guidance.
- Read grocery-label text using Tesseract.js OCR, with detected details available for user review.

Date estimates and visual appearance do not establish food safety. Always follow package instructions and reliable food-storage guidance.

## My contribution

I wrote the Python code independently. I used AI assistance mainly for CSS styling. This is a learning project that I am continuing to improve.

## Technology

Python, Flask, SQLite, HTML, CSS and JavaScript. Tesseract.js provides browser-based OCR. Optional web-push support uses pywebpush.

## Run locally

Use Python 3.10 or newer. Open a terminal in this folder.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open **http://127.0.0.1:8000**. Use the Flask server rather than opening the HTML file directly. A new empty `stivafresh.db` is created automatically. The original database is intentionally not included.

Core grocery tracking needs no API key. OCR needs internet access to download the Tesseract.js library and its recognition assets. Verify detected dates and names before saving them.

## Optional configuration

Copy `.env.example` to `.env` only if configuring optional features. The application loads it locally using python-dotenv. Never upload `.env` or private key files.

### Notifications

Basic in-app expiry reminders require browser permission and the page to be running. A service worker displays the reminder. Web-push subscriptions additionally require your own VAPID keys, a valid contact address, and HTTPS outside localhost. The repository does not contain credentials.

There is a manual `/api/push/test` endpoint. There is **no scheduled background job** that sends expiry reminders while the application is closed. Push delivery and device-specific behaviour need testing with your own configuration.

### Optional vision endpoint

The backend contains `/api/scan-grocery`, which requires an OpenAI API key and API usage billing. The current photo-scan button uses browser OCR and does not call this endpoint. Leave the key blank for ordinary use. This project does not train a machine-learning model.

## Repository layout

```text
app.py
requirements.txt
.env.example
.gitignore
README.md
CHANGELOG.md
templates/
  stivafresh.html
static/
  manifest.json
  service-worker.js
  stivafresh_logo.png
```

The current HTML includes its CSS and JavaScript. Older standalone `style.css` and `script.js` uploads are not used by this template and are excluded to avoid conflicting versions.

## Current limitations

- Local, single-user prototype. There is no account login or user separation: API clients share one grocery database.
- Request validation and error handling need improvement before public hosting.
- Recipes and storage suggestions are rule-based, not personalised AI advice.
- Shelf-life estimates and OCR can be inaccurate.
- Push configuration and the optional paid vision endpoint are not validated by the basic local checks.
- The manifest and service worker do not provide a full offline application. Dedicated square installation icons are still needed for consistent PWA installation support.

Do not expose this development server to the public internet as-is. Public deployment needs authentication, per-user data isolation, input validation and protection of paid API and push endpoints.



A `.gitignore` only prevents new untracked files from being added. If a secret was already committed or publicly shared, remove it from the repository history and rotate that credential. Do not add the original database or private keys later.

No open-source license has been selected yet. Choose one deliberately if you want to grant reuse rights.
