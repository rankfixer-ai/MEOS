import sqlite3

conn = sqlite3.connect('data/meos.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        seed,
        baseline_fitness,
        final_fitness,
        improvement,
        success
    FROM experiments
    WHERE final_fitness IS NOT NULL
''')

rows = cursor.fetchall()

print('Seed | Baseline | Final | Improvement | Success')
print('-----|----------|-------|-------------|--------')

for row in rows:
    seed = row[0]
    baseline = row[1]
    final = row[2]
    improvement = row[3] * 100 if row[3] is not None else 0
    success = '✅' if row[4] == 1 else '❌' if row[4] == 0 else '⏳'
    print(f'{seed:4} | {baseline:.4f} | {final:.4f} | {improvement:5.1f}% | {success}')

conn.close()
