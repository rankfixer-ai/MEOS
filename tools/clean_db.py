import sys, os
sys.path.insert(0, ".")
for f in ["data/meos_v0.3.db", "data/meos_v0.3.db-wal", "data/meos_v0.3.db-shm"]:
    try: os.remove(f)
    except: pass
