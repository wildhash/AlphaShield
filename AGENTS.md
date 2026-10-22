# AGENTS.md

Guidance for AI agents working in this repository.

## Cursor Cloud specific instructions

### Product overview

AlphaShield is a **Python 3.11+** fintech codebase (no Node.js). The main deliverable is the `alphashield` package: multi-agent loan orchestration, trading, RL, and backtesting. There is no long-running HTTP server in the root app; use `python demo.py` for a zero-dependency smoke test. Optional: Streamlit dashboards on port **8501**, hackathon FastAPI under `alphashield-hackathon-assets/` on **8080** (separate `requirements.txt`, may pin outdated packages).

### Virtual environment

- Path: `/workspace/venv`
- Activate: `source /workspace/venv/bin/activate`
- On a fresh Ubuntu VM, `python3 -m venv` requires **`python3.12-venv`** (or matching version) via `apt` once; the VM update script assumes venv already exists or can be created.

### MongoDB (CI / integration tests)

Docker is used for MongoDB (not in the startup update script). After `dockerd` is running:

```bash
sudo docker start alphashield-mongodb 2>/dev/null || sudo docker run -d --name alphashield-mongodb -p 27017:27017 mongo:7.0
export MONGODB_URI=mongodb://localhost:27017/alphashield_test
```

Use `sudo docker` if the daemon socket is root-only. Integration test `tests/integration/test_agent_coordination.py` currently fails collection (`OrchestrationGraph` import); exclude it until fixed.

### Commands (see also `QUICKSTART.md`, `SETUP.md`, `.github/workflows/test.yml`)

| Task | Command |
|------|---------|
| Demo (no API keys) | `source venv/bin/activate && python demo.py` |
| Unit tests (stable subset) | `pytest tests/ --ignore=tests/test_agents_mock.py --ignore=tests/test_populate_sample_data.py --ignore=tests/test_seed_chase_statements.py --ignore=tests/trading/test_backtester.py --ignore=tests/trading/test_data_validator.py --ignore=tests/integration/test_agent_coordination.py -m "not slow"` |
| CI-style tests + coverage | Same as workflow: `MONGODB_URI=... pytest tests/ --cov=... --cov-fail-under=70 -m "not slow"` (may hit collection/coverage failures on `main`) |
| Lint | `ruff check .` and `black --check .` (many pre-existing issues on `main`) |
| Streamlit dashboard | `streamlit run dashboard/app.py` |

### Gotchas

- **`docker compose`**: Root compose maps port **8000** but default command is `demo.py` (CLI only). Profile `dashboard` points at `dashboards/rl_training_dashboard.py` which does not exist; use `dashboard/` locally.
- **`example.py`**: Needs `MONGODB_URI` and `VOYAGE_API_KEY` in `.env` for full multi-agent flow.
- **Alpaca / Voyage**: Optional for most unit tests; some trading tests skip without credentials.
- **Reinstall deps**: Hot reload does not apply to Python package installs; restart processes after `pip install`.
