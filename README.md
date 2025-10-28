# Healthcare Data Quality Monitor

**TL;DR:** Generates synthetic **claims** & **EHR** data, validates with **PySpark + Great Expectations**, enforces a CI **quality gate** in **GitHub Actions**, publishes reports to **S3**, and sends **Slack alerts** on failures.

---

## Why this exists
Bad data breaks dashboards, models, and trust. This repo treats **data quality as code**:
- Checks are versioned in Git
- Runs are automated in CI
- Failures stop the line and notify Slack

---

## What it does
- Creates `claims.csv` and `ehr.csv` on every run
- Validates with Great Expectations (Spark):
  - Column set & schema
  - Non-null checks
  - Value ranges (e.g., HR/SBP/RR; `amount >= 0`)
  - Allowed values (CPT codes)
- **Quality gate:** fails the CI job if any checks fail (optional `force_fail` switch to test alerts)
- **Slack alerts:** posts a message when the gate fails
- **S3 publishing:** uploads HTML reports + `summary.json` per run

---

## Repo layout
dq/
generate_fake_data.py # writes claims.csv & ehr.csv into artifacts/
spark_validate.py # runs GE checks on Spark, writes HTML + summary.json
expectations/
claims_expectations.json # rules for claims
ehr_expectations.json # rules for EHR
.github/workflows/
dq-step1.yml # generate-only (artifact)
dq-step2.yml # Spark + GE (artifact)
dq-step3.yml # upload to S3
dq-step4-quality-gate.yml # main: gate + Slack + S3
README.md 

---

## One-time setup

1) **S3 bucket** in `us-east-1` (example): `yesh-mldev`  
2) **GitHub Secrets** (Repo → Settings → Secrets and variables → Actions):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `SLACK_WEBHOOK_URL` (Slack → “Incoming WebHooks” app → Add to your channel)
3) Confirm bucket name inside `.github/workflows/dq-step4-quality-gate.yml` (`BUCKET: yesh-mldev`).

---

## How to run

- **Main entrypoint:** GitHub → **Actions** → **DQ Step 4 — Quality Gate** → **Run workflow**  
  - Optional input: `force_fail = yes` to test Slack without changing data

**Outputs**
- **S3**: `s3://<bucket>/dq/<run_id>/`
  - `data_docs/claims.html`
  - `data_docs/ehr.html`
  - `summary.json` (pass/fail counts)
- **Slack**: alert with a link to the failed run (only on failures)
- **Logs**: “Print summary” step shows the `summary.json` contents inline

---

## How it works (pipeline)
1) `dq/generate_fake_data.py` → writes CSVs to `artifacts/`
2) `dq/spark_validate.py` → Spark + Great Expectations:
   - Writes minimal HTML reports to `artifacts/data_docs/`
   - Writes `artifacts/summary.json` like:
     ```json
     {"claims":{"total":6,"failed":0},"ehr":{"total":5,"failed":0}}
     ```
3) Workflow computes `failed = claims.failed + ehr.failed`
4) If `failed > 0`: send **Slack alert** + **fail the job**  
   Else: upload HTML + summary to **S3** and **pass**

---

## Customizing checks
Edit JSON in `dq/expectations/*_expectations.json`. Example rule:
```json
{"type": "expect_column_values_to_be_between",
 "kwargs": {"column": "amount", "min_value": 0}}
