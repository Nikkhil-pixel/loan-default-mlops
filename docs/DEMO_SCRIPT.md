# Five-minute viva demo script

Before presenting, start from the repository root, activate the Python 3.11 environment, install dependencies, and ensure the supplied raw dataset is checked out. Keep the MLflow UI in a second terminal. The default local tracking backend is SQLite.

## 0:00–0:40 — Explain the use case and data version

Say: “This is an educational default-risk probability system using the public Kaggle Credit Risk Dataset. It has no date field, so I use stratification rather than a time split. The score is a risk-assessment aid, not an automatic lending decision.”

Show the data pointer and active pipeline:

```bash
git status --short
dvc status
cat data/raw/credit_risk_dataset.csv.dvc
```

Explain that Git stores the DVC pointer while the CSV is held by DVC cache/remote. A logged MLflow model version has the DVC content hash and Git commit attached as tags.

## 0:40–1:40 — Run the pipeline and compare experiments

```bash
dvc repro
cat reports/metrics.json
cat reports/training_summary.json
```

Say: “Cleaning does not impute. Median/mode imputation, optional missing indicators, scaling, one-hot encoding, and the selected classifier all live in one sklearn Pipeline. Three candidate families are trained on the same stratified split, with imbalance handled from training data.”

If the UI is not running, start it in a second terminal:

```bash
mlflow ui --backend-store-uri "$MLFLOW_TRACKING_URI" --host 0.0.0.0 --port "$MLFLOW_PORT"
```

Open `http://localhost:5000` (or the configured port), select the `loan-default-risk` experiment, and compare ROC-AUC/PR-AUC/KS and the saved ROC, precision-recall, and confusion-matrix artifacts. The experiment and registered model names are configurable in `params.yaml`.

## 1:40–2:20 — Promote safely

```bash
python -m src.promote
```

Show the console decision. Explain that first deployment assigns the best candidate the champion alias. Later promotion requires the configured metric margin; a candidate that misses the margin is assigned the challenger alias. The service loads aliases rather than deprecated MLflow model stages.

## 2:20–3:20 — Call and validate the API

Start the service in another terminal:

```bash
uvicorn app.main:app --host "$API_HOST" --port "$API_PORT"
```

Then run:

```bash
curl -sS "http://localhost:${API_PORT}/health"
curl -sS "http://localhost:${API_PORT}/model-info"
curl -sS -X POST "http://localhost:${API_PORT}/predict" -H 'Content-Type: application/json' \
  -d '{"person_age":30,"person_income":50000,"person_home_ownership":"RENT","person_emp_length":5,"loan_intent":"EDUCATION","loan_grade":"B","loan_amnt":10000,"loan_int_rate":11.5,"loan_percent_income":0.2,"cb_person_default_on_file":"N","cb_person_cred_hist_length":5}'
curl -sS -X POST "http://localhost:${API_PORT}/predict" -H 'Content-Type: application/json' \
  -d '{"person_age":144}'
```

Point out the probability/risk band in the valid response and the 422 from the invalid body. Explain that Pydantic's input schema is generated from the same YAML as training, and successful requests are logged with model/data provenance.

## 3:20–4:10 — Show clean and drifted monitoring

```bash
rm -f "$LOG_FILE"
python -m src.simulate_drift --clean
python -m src.monitor
cat reports/drift_summary.json
rm -f "$LOG_FILE"
python -m src.simulate_drift
python -m src.monitor
cat reports/drift_summary.json
```

Open `reports/data_drift.html`. Explain that the first request sample comes from reference data; the second intentionally shifts configured income and interest-rate values. The JSON summary makes drift suitable for automation, while too few requests produces `insufficient_data` rather than an unsupported drift claim.

## 4:10–5:00 — CI/CD and controlled updates

Open `.github/workflows/ci.yml` and `.github/workflows/retrain.yml` in the repository (or show their runs in the Actions tab). Explain: CI lint/tests/train-smokes/builds on pull requests; main may publish to GHCR. The weekly/manual retraining workflow monitors first, runs DVC retraining on drift or an explicit force request, then pauses at the `model-production` GitHub Environment. Required reviewers approve before `src.promote` updates the champion alias. Credentials come from GitHub Secrets; they are not checked into the project.

Close with the limitations: public synthetic-style data, no time dimension, no fairness or production validation, and a probabilistic output that requires domain review before any real use.
