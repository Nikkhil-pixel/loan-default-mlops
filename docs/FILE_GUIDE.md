# File guide

This guide maps the repository from input data to monitored serving. The design keeps feature names, thresholds, model settings, and runtime paths in `params.yaml` and routes configuration through `src/config.py`.

| File or folder | What it does and why it exists |
|---|---|
| `README.md` | Main setup, usage, configuration reference, system flow, dataset caveats, and troubleshooting. |
| `params.yaml` | Single human-editable source for feature/target definitions, categories/ranges, cleaning rules, batch fractions, model hyperparameters, MLflow aliases, risk bands, output paths, and test fixture locations. |
| `.env.example` | Lists local/Docker environment overrides. Copy it to `.env`; never commit the real file. |
| `src/config.py` | Shared loader used by scripts and the API; reads YAML, expands environment placeholders, and resolves project-relative paths. |
| `src/prepare.py` | Removes exact duplicates, impossible ages, and implausibly long employment histories. It deliberately leaves missing values for pipeline-time imputation. |
| `src/make_batches.py` | Splits rows into reproducible stratified increments and writes cumulative snapshots for data-version demonstrations. |
| `src/train.py` | Makes one stratified split, builds the same preprocessing/model pipeline for each configured estimator, logs experiments and artifacts, and registers model versions tagged with data/Git provenance. |
| `src/metrics.py` | Shared ROC-AUC, PR-AUC, KS, threshold, and confusion-matrix calculations, plus plot/artifact output. |
| `src/evaluate.py` | Loads the chosen run's pipeline, evaluates the held-out data, updates the run artifacts, and writes a DVC metric report. |
| `src/promote.py` | Compares registered versions and uses MLflow aliases to promote only when a candidate meets the configured improvement margin. |
| `src/monitor.py` | Reads reference features and prediction JSONL records, runs Evidently, saves HTML, and writes a compact drift decision JSON. |
| `src/simulate_drift.py` | Creates either clean reference-like or deliberately shifted request records so drift behavior can be demonstrated without sending real requests. |
| `app/schemas.py` | Dynamically creates a strict Pydantic request model from configured feature names, numeric ranges, and category lists. |
| `app/main.py` | FastAPI service. It loads the champion alias, validates requests, returns probability/risk details, supports reload/model info, and handles unavailable models gracefully. |
| `app/logger.py` | Appends timestamped predictions and model metadata to the configured JSONL file safely. |
| `tests/fixtures/credit_risk_sample.csv` | Small balanced sample derived from the supplied dataset for quick CI and validation. The full raw CSV remains DVC managed. |
| `tests/test_prepare.py` | Checks duplicate removal, configured outlier filtering, and preservation of missing values. |
| `tests/test_schema.py` | Checks that valid records pass and invalid ranges/categories/extra fields fail. |
| `tests/test_api.py` | Exercises health, prediction, batch, model information, reload, and HTTP 422 validation behavior with a deterministic test classifier. |
| `tests/test_config_no_hardcode.py` | Scans `src/` and `app/` for configured identifiers and paths that should not be embedded in code. |
| `tests/test_promote.py` | Uses a temporary SQLite MLflow registry to verify first promotion and weaker-candidate challenger assignment. |
| `dvc.yaml` and `dvc.lock` | Declare the `prepare -> train -> evaluate` DAG and record resolved inputs, outputs, and parameters after a DVC run. |
| `data/raw/credit_risk_dataset.csv.dvc` | Small Git pointer for the original dataset; DVC stores the actual CSV in its cache/remote. |
| `data/processed/` | Holds the cleaned dataset and reproducible train/test split produced by DVC stages. These outputs are not ordinary source files. |
| `data/batches/` | Holds cumulative snapshots produced by `make_batches.py`; add them with DVC when demonstrating data versions. |
| `.dvc/config` | DVC's repository configuration and local default remote. Remote-specific credentials should be local-only or supplied as CI secrets. |
| `.dvcignore` | Keeps DVC internals out of data discovery. |
| `.gitignore` | Excludes local data artifacts, caches, runtime logs, SQLite state, secrets, and generated reports while keeping DVC pointers tracked. |
| `requirements.txt` | Exact direct dependency versions for Python 3.11 including FastAPI, DVC, MLflow, Evidently 0.4.40, XGBoost, and scikit-learn. |
| `requirements-shap.txt` | Optional pinned SHAP dependency set used only when the configured explanation flag is enabled. |
| `pyproject.toml` | Ruff lint rules and pytest defaults. |
| `Dockerfile` | Builds the same Python service as a slim non-root container and defines an environment-based health check. |
| `docker-compose.yml` | Starts MLflow and the prediction API, configures ports/tracking endpoints from environment, and shares persistent logs/artifact/registry volumes. |
| `.github/workflows/ci.yml` | Runs lint, fixture training, tests, Docker build, and main-branch-only GHCR publication. |
| `.github/workflows/retrain.yml` | Schedules or manually requests monitoring; retrains if drift is found (or forced), then waits for the protected production Environment before promotion. |
| `notebooks/eda.ipynb` | Lightweight exploratory notebook for shape, missingness, class balance, and selected numeric summaries using the same configuration. |
| `logs/` and `reports/` | Runtime request records and human/machine-readable evaluation/drift outputs. The DVC metrics file is deliberately not ignored; transient reports and summaries are excluded from ordinary Git commits. |
| `docs/DEMO_SCRIPT.md` | Time-boxed commands and narration for presenting the system in a viva. |
