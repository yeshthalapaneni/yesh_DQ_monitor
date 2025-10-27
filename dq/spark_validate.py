import json, pathlib, shutil
from pyspark.sql import SparkSession
import great_expectations as ge
from great_expectations.dataset.sparkdf_dataset import SparkDFDataset

art = pathlib.Path("artifacts"); art.mkdir(exist_ok=True)
docs = art/"data_docs"
if docs.exists(): shutil.rmtree(docs)
docs.mkdir(parents=True, exist_ok=True)

spark = (SparkSession.builder
         .appName("DQ-Spark-GE")
         .config("spark.ui.showConsoleProgress","false")
         .getOrCreate())

def run_suite(csv_path, exp_path, name):
    df = spark.read.option("header","true").option("inferSchema","true").csv(str(csv_path))
    gdf = SparkDFDataset(df)
    exps = json.loads(pathlib.Path(exp_path).read_text())["expectations"]
    results = []
    for e in exps:
        etype, kwargs = e["type"], e["kwargs"]
        ret = getattr(gdf, etype)(**kwargs)         # <— returns an object with .success
        success = bool(getattr(ret, "success", False))
        results.append({"expectation": etype, "kwargs": kwargs, "success": success})
    # basic HTML report
    html = ["<h2>Report: "+name+"</h2><ul>"]
    html += [f"<li>{r['expectation']} — <b>{'PASS' if r['success'] else 'FAIL'}</b></li>" for r in results]
    html.append("</ul>")
    (docs/f"{name}.html").write_text("\n".join(html))
    return results


claims_res = run_suite(art/"claims.csv", "dq/expectations/claims_expectations.json", "claims")
ehr_res    = run_suite(art/"ehr.csv",    "dq/expectations/ehr_expectations.json",    "ehr")

summary = {
  "claims": {"total": len(claims_res), "failed": sum(1 for r in claims_res if not r["success"])},
  "ehr":    {"total": len(ehr_res),    "failed": sum(1 for r in ehr_res if not r["success"])}
}
(pathlib.Path("artifacts/summary.json")).write_text(json.dumps(summary, indent=2))
print("Summary:", summary)

spark.stop()
