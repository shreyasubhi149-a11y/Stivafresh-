# GitHub preparation changes

- Organised the current HTML under Flask's `templates/` directory.
- Replaced `.gitignore.txt` with a proper `.gitignore` covering credentials, local databases and Python environments.
- Excluded the original `.env`, both PEM key files and SQLite database. Added placeholder-only `.env.example`.
- Added python-dotenv loading for optional local environment configuration.
- Changed direct startup to localhost with debug disabled.
- Used the uploaded manifest and service worker. Corrected the manifest start URL and missing icon paths, and added a listener for the current template's in-app expiry-reminder messages. No offline cache was introduced.
- Retained the supplied logo as a static asset. The template does not currently display it.
- Kept the supplied application features and database schema. Excluded unused legacy standalone frontend files.

The original uploaded files have not been modified. No GitHub repository was published by this preparation step.
