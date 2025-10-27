import pandas as pd, numpy as np, pathlib

out = pathlib.Path("artifacts"); out.mkdir(exist_ok=True)

# claims.csv — simple claims table with a few intentional issues
rng = np.random.default_rng(42); N = 500
claims = pd.DataFrame({
  "claim_id": np.arange(1, N+1),
  "patient_id": rng.integers(1000, 2000, N),
  "amount": np.round(rng.normal(250, 80, N).clip(10, 2000), 2),
  "cpt_code": rng.choice(["99213","93000","80050","12001","70450"], N),
  "paid": rng.choice([0,1], N, p=[0.2,0.8]),
  "dt": pd.to_datetime("today").normalize()
})
# add a few nulls to test data quality checks
claims.to_csv(out/"claims.csv", index=False)

# ehr.csv — simple vitals table with a few nulls
ehr = pd.DataFrame({
  "encounter_id": np.arange(1, N+1),
  "patient_id": rng.integers(1000, 2000, N),
  "hr": rng.normal(82, 14, N).clip(40, 180),
  "sbp": rng.normal(118, 20, N).clip(70, 220),
  "rr": rng.normal(18, 4, N).clip(6, 40)
})
ehr.to_csv(out/"ehr.csv", index=False)

print("Wrote:", [p.name for p in out.iterdir()])
