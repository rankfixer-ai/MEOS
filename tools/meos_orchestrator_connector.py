import sys, os, json, time
sys.path.insert(0, ".")

from supabase import create_client
from dotenv import load_dotenv
load_dotenv("C:/Users/acibr/Desktop/Projects/Active/RisePinas/rise-orchestrator/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

from src.core.meos_v0_3_core import MutationEngine, FitnessFunction
from src.selection.selection_engine import SelectionEngine

CONFIG_PATH = "C:/Users/acibr/Desktop/Projects/Active/RisePinas/rise-orchestrator/.env"

# === GENOME ===
def read_config():
    config = {}
    with open(CONFIG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                try: config[k] = int(v)
                except: config[k] = v
    return config

def write_config(genome):
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()
    with open(CONFIG_PATH, "w") as f:
        for line in lines:
            written = False
            for k, v in genome.items():
                if line.startswith(k + "="):
                    f.write(f"{k}={v}\n")
                    written = True
                    break
            if not written:
                f.write(line)

# === FITNESS ===
def get_fitness():
    metrics = supabase.table("metrics_history").select("subsystem,name,value").order("recorded_at", desc=True).limit(20).execute()
    data = {}
    for m in metrics.data:
        data[f"{m['subsystem']}.{m['name']}"] = float(m["value"])
    
    total = data.get("ingestion.total_jobs", 1)
    added = data.get("ingestion.jobs_added_24h", 0)
    freshness = data.get("ingestion.job_freshness_hours", 99)
    missing_loc = data.get("ingestion.missing_location", 0)
    missing_sal = data.get("ingestion.missing_salary", 0)
    alerts = data.get("alerts.alert_matched", 0)
    
    return (
        (added / max(1, total)) * 0.25 +
        (1 / (1 + freshness)) * 0.25 +
        (1 - (missing_loc + missing_sal) / max(1, total * 2)) * 0.25 +
        (alerts / max(1, total)) * 0.15 +
        0.10
    )

# === MEOS ===
mutator = MutationEngine(random_seed=42)
selector = SelectionEngine(target_threshold=0.5)
genome = {
    "CYCLE_INTERVAL_MINUTES": 15,
    "SCRAPER_TIMEOUT_SECONDS": 30,
    "MAX_RETRIES": 3,
}
best_genome = genome.copy()
best_fitness = 0

print("MEOS Orchestrator Optimizer - optimizing RisePinas config\n")

for gen in range(20):
    # Custom mutation: only mutate our 3 real parameters
    new_genome = genome.copy()
    param = mutator.random.choice(["CYCLE_INTERVAL_MINUTES", "SCRAPER_TIMEOUT_SECONDS", "MAX_RETRIES"])
    if param == "CYCLE_INTERVAL_MINUTES":
        new_genome[param] = mutator.random.choice([5, 10, 15, 20, 30, 45, 60])
    elif param == "SCRAPER_TIMEOUT_SECONDS":
        new_genome[param] = mutator.random.choice([10, 15, 30, 45, 60, 90, 120])
    else:
        new_genome[param] = mutator.random.choice([1, 2, 3, 5, 7, 10])
    
    # Ensure valid ranges
    new_genome["CYCLE_INTERVAL_MINUTES"] = max(5, min(60, new_genome.get("CYCLE_INTERVAL_MINUTES", 15)))
    new_genome["SCRAPER_TIMEOUT_SECONDS"] = max(10, min(120, new_genome.get("SCRAPER_TIMEOUT_SECONDS", 30)))
    new_genome["MAX_RETRIES"] = max(1, min(10, new_genome.get("MAX_RETRIES", 3)))
    
    write_config(new_genome)
    print(f"[GEN {gen+1:2d}] interval={new_genome['CYCLE_INTERVAL_MINUTES']}m timeout={new_genome['SCRAPER_TIMEOUT_SECONDS']}s retries={new_genome['MAX_RETRIES']} ...waiting for orchestrator cycle...")
    
    time.sleep(new_genome["CYCLE_INTERVAL_MINUTES"] * 60)
    
    fitness = get_fitness()
    print(f"         fitness={fitness:.4f}", end="")
    
    if fitness > best_fitness:
        best_fitness = fitness
        best_genome = new_genome.copy()
        genome = new_genome.copy()
        print("  NEW BEST")
    else:
        print("")
    
    if gen % 5 == 0:
        print(f"  >> Best so far: {best_genome} | fitness={best_fitness:.4f}")

print(f"\nOPTIMAL CONFIG: {best_genome}")
print(f"Best fitness: {best_fitness:.4f}")
write_config(best_genome)
print("Optimal config written to .env")
