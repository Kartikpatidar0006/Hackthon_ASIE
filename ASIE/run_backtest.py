"""Quick backtest script to measure model accuracy."""
import pandas as pd
from asie.etl.pipeline import ETLPipeline
from asie.backtesting import BacktestEngine

pipeline = ETLPipeline()
print("Loading data...")
df = pd.read_parquet("data/signals.parquet")
print(f"Loaded {len(df)} signals")

bt = BacktestEngine(min_train_months=24, test_months=12)

test_skills = [
    "python", "machine_learning", "react", "docker", "cybersecurity",
    "quantum_computing", "golang", "sql", "deep_learning", "cloud_computing",
]

header = f"{'Skill':<25} {'MAPE%':<10} {'RMSE':<10} {'MAE':<10} {'DirAcc%':<10}"
print()
print(header)
print("-" * 65)

total_mape = 0
total_rmse = 0
total_mae = 0
total_dir = 0
count = 0

for sk in test_skills:
    ts = pipeline.get_skill_timeseries(df, sk)
    if ts.empty or len(ts) < 36:
        print(f"{sk:<25} SKIP (insufficient data)")
        continue
    result = bt.run(ts, sk, n_splits=3)
    mape_str = f"{result.mape:.2f}"
    rmse_str = f"{result.rmse:.4f}"
    mae_str = f"{result.mae:.4f}"
    dir_str = f"{result.directional_accuracy * 100:.1f}"
    print(f"{sk:<25} {mape_str:<10} {rmse_str:<10} {mae_str:<10} {dir_str:<10}")
    total_mape += result.mape
    total_rmse += result.rmse
    total_mae += result.mae
    total_dir += result.directional_accuracy
    count += 1

print("-" * 65)
if count > 0:
    avg_mape = total_mape / count
    avg_rmse = total_rmse / count
    avg_mae = total_mae / count
    avg_dir = total_dir / count * 100
    print(f"{'AVERAGE':<25} {avg_mape:<10.2f} {avg_rmse:<10.4f} {avg_mae:<10.4f} {avg_dir:<10.1f}")
    print()
    print(f"Overall Model Accuracy: {100 - avg_mape:.1f}%")
    print(f"Directional Accuracy:   {avg_dir:.1f}%")
