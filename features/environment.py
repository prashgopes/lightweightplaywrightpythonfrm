import json
import logging
import os
import re
import time
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

from pages.login_page import LoginPage


ROOT = Path(__file__).resolve().parents[1]


def _load_credentials() -> dict[str, str]:
    credentials_path = ROOT / "config" / "env.json"
    credentials: dict[str, str] = {}
    if credentials_path.exists():
        with credentials_path.open(encoding="utf-8") as credentials_file:
            credentials = json.load(credentials_file)

    username = os.environ.get("NAUKRI_USERNAME") or credentials.get("username")
    password = os.environ.get("NAUKRI_PASSWORD") or credentials.get("password")
    if not username or not password:
        raise RuntimeError(
            "Naukri credentials are missing. Set NAUKRI_USERNAME and "
            "NAUKRI_PASSWORD or create the ignored config/env.json file."
        )
    return {"username": username, "password": password}


def _worker_id(context) -> str:
    metadata = getattr(context, "behavex", None)
    return str(getattr(metadata, "worker_id", "local"))


def before_all(context) -> None:
    with (ROOT / "config" / "app_config.json").open(encoding="utf-8") as config_file:
        app_config = json.load(config_file)

    context.base_url = app_config["base_url"]
    context.credentials = _load_credentials()
    context.results = []
    context.run_dir = Path(os.environ["TEST_RUN_DIR"])
    context.run_dir.mkdir(parents=True, exist_ok=True)

    worker = _worker_id(context)
    context.worker_id = worker
    log_dir = Path(os.environ["TEST_LOG_DIR"])
    log_path = log_dir / f"worker-{worker}-{os.getpid()}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    context.logger = logging.getLogger(f"behave.worker.{worker}.{os.getpid()}")
    context.logger.setLevel(logging.INFO)
    context.logger.propagate = False
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    context.logger.addHandler(handler)

    context.playwright = sync_playwright().start()
    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() not in {
        "0",
        "false",
        "no",
    }
    context.browser = context.playwright.chromium.launch(headless=headless)
    context.logger.info("Started test worker %s", worker)


def before_scenario(context, scenario) -> None:
    context.scenario_started = time.perf_counter()
    context.browser_context = context.browser.new_context()
    context.page = context.browser_context.new_page()
    context.login_page = LoginPage(context.page, context.base_url)
    context.logger.info("Starting scenario: %s", scenario.name)


def after_scenario(context, scenario) -> None:
    status = scenario.status.name
    duration = time.perf_counter() - context.scenario_started
    record = {
        "name": scenario.name,
        "feature": scenario.feature.name,
        "status": status,
        "duration_seconds": round(duration, 3),
        "worker": context.worker_id,
    }
    if status == "failed":
        snapshot_dir = Path(os.environ["TEST_SNAPSHOT_DIR"])
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", scenario.name).strip("-") or "scenario"
        snapshot_path = snapshot_dir / f"{safe_name}-{uuid.uuid4().hex[:8]}.png"
        context.page.screenshot(path=str(snapshot_path), full_page=True)
        record["snapshot"] = str(snapshot_path)
        context.logger.error("Scenario failed: %s; snapshot: %s", scenario.name, snapshot_path)
    else:
        context.logger.info("Scenario %s: %s (%.3fs)", status, scenario.name, duration)

    context.results.append(record)
    context.browser_context.close()


def after_all(context) -> None:
    context.browser.close()
    context.playwright.stop()
    context.logger.info("Finished test worker %s", context.worker_id)
    for handler in context.logger.handlers[:]:
        handler.close()
        context.logger.removeHandler(handler)

    result_path = context.run_dir / f"worker-{context.worker_id}-{os.getpid()}.json"
    result_path.write_text(json.dumps(context.results, indent=2), encoding="utf-8")
