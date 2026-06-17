import sqlite3

def fmt(val):
    if val is None:
        return "   N/A  "
    return f"{val:8.4f}"

conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

print("\n" + "=" * 100)
print("📊 FAILED SEEDS WITH METRICS (42, 9001)")
print("=" * 100)

# Check if columns exist
cursor.execute("PRAGMA table_info(mutation_trials)")
columns = [col[1] for col in cursor.fetchall()]
has_gen_score = 'generalization_score' in columns
has_stability = 'stability_score' in columns
has_env = all(c in columns for c in ['environment_small', 'environment_medium', 'environment_large'])

# Build query based on available columns
query = '''
SELECT
    seed,
    generation,
    ROUND(fitness_after, 4) as fitness,
    evaluation_result
'''

if has_gen_score:
    query += ', ROUND(generalization_score, 4) as gen_score'
else:
    query += ', NULL as gen_score'

if has_stability:
    query += ', ROUND(stability_score, 4) as stability'
else:
    query += ', NULL as stability'

if has_env:
    query += ', ROUND(environment_small, 4) as small, ROUND(environment_medium, 4) as medium, ROUND(environment_large, 4) as large'
else:
    query += ', NULL as small, NULL as medium, NULL as large'

query += '''
FROM mutation_trials
WHERE seed IN (42, 9001)
ORDER BY seed, generation
'''

cursor.execute(query)
rows = cursor.fetchall()

if not rows:
    print("No data found for seeds 42 and 9001.")
    print("Note: These seeds failed, so they may not have recorded metrics yet.")
    print("Run the migration and re-run the seeds to capture metrics.")
    conn.close()
    exit()

# Determine what to print based on available columns
header = f'{"Seed":>6} | {"Gen":>4} | {"Fitness":>8} | {"Result":>20}'
if has_gen_score:
    header += ' | {"Gen Score":>10}'
if has_stability:
    header += ' | {"Stability":>10}'
if has_env:
    header += ' | {"Small":>8} | {"Medium":>8} | {"Large":>8}'

print(header)
print("-" * len(header))

for row in rows:
    seed = row[0]
    gen = row[1]
    fitness = row[2]
    result = row[3]
    idx = 4
    
    line = f'{seed:6} | {gen:4} | {fitness:8.4f} | {result:20}'
    
    if has_gen_score:
        val = row[idx]
        line += f' | {fmt(val)}'
        idx += 1
    if has_stability:
        val = row[idx]
        line += f' | {fmt(val)}'
        idx += 1
    if has_env:
        small = row[idx]
        medium = row[idx+1]
        large = row[idx+2]
        line += f' | {fmt(small)} | {fmt(medium)} | {fmt(large)}'
    
    print(line)

conn.close()
