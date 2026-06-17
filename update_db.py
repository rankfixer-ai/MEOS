import sqlite3
conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

# Update evaluation_result values
cursor.execute("UPDATE mutation_trials SET evaluation_result = 'ACCEPTED_EVOLUTION' WHERE evaluation_result = 'PROMOTED'")
cursor.execute("UPDATE mutation_trials SET evaluation_result = 'COMPENSATORY_STABILITY_PROMOTION' WHERE evaluation_result = 'PROMOTED'")

conn.commit()
conn.close()
print('✅ Database updated with new selection statuses')
