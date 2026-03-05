# tests/rl/test_train_nightly_logs_dir.py
"""Tests that the nightly training job creates the logs directory before logging."""
import importlib
import logging
import os
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path


def test_logs_directory_created_before_filehandler(tmp_path, monkeypatch):
    """
    Importing train_nightly must create the logs/ directory before the
    FileHandler is opened, so that no FileNotFoundError is raised even
    when the directory does not yet exist.
    """
    # Run the directory-creation logic in a temp working directory so
    # the test does not pollute the repository.
    monkeypatch.chdir(tmp_path)

    logs_dir = tmp_path / "logs"
    assert not logs_dir.exists(), "logs/ should not exist before import"

    # Remove any cached module so we get a fresh import.
    sys.modules.pop("jobs.train_nightly", None)

    # Patch get_mongo_client to avoid a real DB connection.
    with mock.patch("alphashield.database.mongodb_client.get_mongo_client", return_value=None):
        # The import itself triggers logging.basicConfig with a FileHandler.
        # If os.makedirs is called first the import must succeed without error.
        import jobs.train_nightly  # noqa: F401

    assert logs_dir.exists(), "logs/ directory must be created on import"


def test_nightly_trainer_runs_without_logs_dir(tmp_path, monkeypatch):
    """
    NightlyTrainer.run() must work even if the process starts in a
    directory that has no logs/ sub-directory.
    """
    monkeypatch.chdir(tmp_path)
    sys.modules.pop("jobs.train_nightly", None)

    with mock.patch("alphashield.database.mongodb_client.get_mongo_client", return_value=None):
        import jobs.train_nightly as tn

    trainer = tn.NightlyTrainer(db_client=None, dry_run=True)
    # No agents means default list; all will be skipped (no replay data).
    results = trainer.run()

    assert isinstance(results, dict)
    for agent_result in results.values():
        assert agent_result.get("status") in ("skipped", "error", "success")
