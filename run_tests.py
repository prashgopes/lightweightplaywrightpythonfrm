import argparse
import html
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def write_report(report_dir: Path, execution_time_seconds: float) -> dict:
    scenarios = []
    for result_file in sorted(report_dir.glob("worker-*.json")):
        scenarios.extend(json.loads(result_file.read_text(encoding="utf-8")))

    passed = sum(result["status"] == "passed" for result in scenarios)
    failed = sum(result["status"] == "failed" for result in scenarios)
    summary = {
        "scripts_executed": len(scenarios),
        "passed": passed,
        "failed": failed,
        "execution_time_seconds": round(execution_time_seconds, 3),
        "scenario_time_seconds": round(
            sum(result["duration_seconds"] for result in scenarios), 3
        ),
        "scenarios": scenarios,
    }
    (report_dir / "report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    rows = "\n".join(
        "<tr><td>{feature}</td><td>{name}</td><td>{status}</td>"
        "<td>{duration:.3f}s</td><td>{worker}</td></tr>".format(
            feature=html.escape(result["feature"]),
            name=html.escape(result["name"]),
            status=html.escape(result["status"]),
            duration=result["duration_seconds"],
            worker=html.escape(result["worker"]),
        )
        for result in scenarios
    )
    report_html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Test execution report</title>
<style>body{{font:15px Arial,sans-serif;margin:2rem}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:.6rem;text-align:left}}th{{background:#eee}}</style></head>
<body><h1>Test execution report</h1>
<p>Scripts executed: {len(scenarios)} | Passed: {passed} | Failed: {failed} |
Execution time: {summary["execution_time_seconds"]:.3f}s |
Combined scenario time: {summary["scenario_time_seconds"]:.3f}s</p>
<table><thead><tr><th>Feature</th><th>Scenario</th><th>Status</th>
<th>Duration</th><th>Worker</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
    (report_dir / "report.html").write_text(report_html, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Naukri Behave/Playwright tests.")
    parser.add_argument(
        "--parallel", action="store_true", help="Run scenarios with BehaveX."
    )
    parser.add_argument(
        "--headed", action="store_true", help="Show the Chromium browser window."
    )
    parser.add_argument(
        "--processes", type=int, default=2, help="BehaveX worker count (default: 2)."
    )
    parser.add_argument("behave_args", nargs="*", help="Additional Behave arguments.")
    args, forwarded_args = parser.parse_known_args()
    if args.processes < 1:
        parser.error("--processes must be at least 1")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    report_dir = ROOT / "reports" / run_id
    log_dir = ROOT / "logs" / run_id
    snapshot_dir = ROOT / "snapshots" / run_id
    for directory in (report_dir, log_dir, snapshot_dir):
        directory.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment.update(
        {
            "TEST_RUN_DIR": str(report_dir),
            "TEST_LOG_DIR": str(log_dir),
            "TEST_SNAPSHOT_DIR": str(snapshot_dir),
            "PLAYWRIGHT_HEADLESS": "false" if args.headed else "true",
        }
    )
    feature_paths = args.behave_args or ["features"]
    if args.parallel:
        executable = Path(sys.executable).parent / (
            "behavex.exe" if os.name == "nt" else "behavex"
        )
        if not executable.exists():
            parser.error("BehaveX is not installed; install requirements.txt first.")
        command = [
            str(executable),
            f"--parallel-processes={args.processes}",
            "--parallel-scheme=scenario",
            "--no-report",
            *feature_paths,
            *forwarded_args,
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "behave",
            *feature_paths,
            *forwarded_args,
        ]

    print(f"Execution artifacts: {report_dir}")
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    execution_time = time.perf_counter() - started
    summary = write_report(report_dir, execution_time)
    print(
        "Scenarios: {scripts_executed}, passed: {passed}, failed: {failed}, "
        "execution time: {execution_time_seconds:.3f}s".format(**summary)
    )
    print(f"HTML report: {report_dir / 'report.html'}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
