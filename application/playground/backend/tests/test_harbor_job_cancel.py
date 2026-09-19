"""cancel_job stops the harbor process and keeps finished trials on disk.

Background: the cockpit's Stop button used to call DELETE, which removed the job
directory with every finished trial in it. Cancel must never touch jobs/<job>.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

from backend.service.harbor_job_service import HarborJobService, HarborLaunchRecord


def _service(tmp_path):
    repo = tmp_path / "repo"
    jobs_dir = repo / "jobs"
    jobs_dir.mkdir(parents=True)
    return HarborJobService(
        repo_root=repo,
        jobs_dir=jobs_dir,
        generated_configs_dir=repo / "configs" / "jobs" / "application-task-job-recipe",
        harbor_command=("echo", "harbor"),
    )


def test_cancel_job_terminates_process_and_keeps_trials(tmp_path, monkeypatch):
    service = _service(tmp_path)
    job_name = "pg-web-demo-1234abcd"
    job_dir = service.jobs_dir / job_name
    trial = job_dir / "web_demo__abc1234"
    trial.mkdir(parents=True)
    (trial / "result.json").write_text(json.dumps({"finished_at": "2026-09-19T00:00:00"}))
    (job_dir / "config.json").write_text("{}")

    # No docker in unit tests: the container sweep must degrade to "nothing removed".
    monkeypatch.setattr("backend.service.harbor_job_service._remove_trial_containers", lambda _job_dir: 0)

    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    service._launches[job_name] = HarborLaunchRecord(job_name=job_name, status="running", process=proc)

    result = service.cancel_job(job_name)

    assert result["cancelled"] is True
    assert result["status"] == "cancelled"
    deadline = time.time() + 5
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.05)
    assert proc.poll() is not None, "harbor process should have been terminated"
    record = service._launches[job_name]
    assert record.status == "cancelled"
    assert record.cancel_requested is True
    # The whole point: nothing under jobs/<job> is removed.
    assert (trial / "result.json").is_file()
    assert (job_dir / "config.json").is_file()


def test_cancel_job_is_noop_when_not_running(tmp_path):
    service = _service(tmp_path)
    service._launches["pg-web-done"] = HarborLaunchRecord(job_name="pg-web-done", status="completed")
    assert service.cancel_job("pg-web-done") == {"jobName": "pg-web-done", "cancelled": False, "status": "completed"}


def test_cancel_job_unknown_job(tmp_path):
    service = _service(tmp_path)
    try:
        service.cancel_job("pg-web-missing")
    except ValueError as exc:
        assert "not found" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
