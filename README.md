# Lightweight Naukri UI test framework

This project uses Python, Behave (Gherkin BDD), Playwright, and the Page Object
Model. Local runs use Behave sequentially; GitHub Actions runs scenarios in
parallel with BehaveX.

## Local setup (Windows PowerShell)

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Local credentials are read from `config/env.json`. That file is ignored by Git;
keep it on your machine and never commit it. The repository includes the local
file only in the working copy where it was created. The URL is configured in
`config/app_config.json`.

Run locally:

```powershell
python run_tests.py
```

Run a specific feature with a visible browser:

```powershell
python run_tests.py --headed features/login.feature
```

Run with BehaveX parallel workers locally:

```powershell
python run_tests.py --parallel --processes 2
```

Each execution creates a timestamped directory under `reports`, `logs`, and
`snapshots`. The report directory contains `report.html` and `report.json`.
Reports show scenarios executed, pass/fail counts, scenario execution time, and
the worker for each scenario. Failed scenarios save a screenshot under the
matching snapshots run directory. Worker log files are stored under the matching
logs run directory.

## GitHub Actions

Add repository Actions secrets named `NAUKRI_USERNAME` and `NAUKRI_PASSWORD`.
Then use **Actions → Naukri UI tests → Run workflow**. The workflow installs
Playwright's Chromium browser and required Linux dependencies, executes tests
with two BehaveX workers, and uploads reports, logs, and failure screenshots as
workflow artifacts.
