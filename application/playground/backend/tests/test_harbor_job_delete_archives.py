"""delete_job must never erase trial data: it moves the job to jobs/.trash."""
from __future__ import annotations

from backend.service.harbor_job_service import HarborJobService


def test_delete_job_moves_to_trash(tmp_path):
    repo = tmp_path / "repo"
    jobs = repo / "jobs"
    (jobs / "pg-web-demo-1234abcd" / "web_demo__abc1234").mkdir(parents=True)
    (jobs / "pg-web-demo-1234abcd" / "web_demo__abc1234" / "result.json").write_text("{}")
    service = HarborJobService(repo_root=repo, jobs_dir=jobs, generated_configs_dir=repo / "configs" / "jobs" / "x", harbor_command=("echo", "harbor"))
    service.delete_job("pg-web-demo-1234abcd")
    assert not (jobs / "pg-web-demo-1234abcd").exists()
    archived = list((jobs / ".trash").glob("pg-web-demo-1234abcd-*"))
    assert len(archived) == 1
    assert (archived[0] / "web_demo__abc1234" / "result.json").is_file()
