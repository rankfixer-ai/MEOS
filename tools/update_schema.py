import sqlite3
conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

# Add missing columns
try:
    cursor.execute("ALTER TABLE mutation_trials ADD COLUMN stability_before REAL")
    print('✅ Added stability_before')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('ℹ️ stability_before already exists')
    else:
        print(f'Error: {e}')

try:
    cursor.execute("ALTER TABLE mutation_trials ADD COLUMN stability_after REAL")
    print('✅ Added stability_after')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('ℹ️ stability_after already exists')
    else:
        print(f'Error: {e}')

try:
    cursor.execute("ALTER TABLE mutation_trials ADD COLUMN combined_score REAL")
    print('✅ Added combined_score')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('ℹ️ combined_score already exists')
    else:
        print(f'Error: {e}')

conn.commit()
conn.close()
print('✅ Database schema updated')
