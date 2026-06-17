import sqlite3
conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

# Drop dependent views and tables
cursor.execute('DROP VIEW IF EXISTS promotion_audit')
cursor.execute('DROP VIEW IF EXISTS gene_effects')
cursor.execute('DROP TABLE IF EXISTS mutation_trials_new')
cursor.execute('DROP TABLE IF EXISTS mutation_trials')

# Recreate mutation_trials with correct schema
cursor.execute('''
CREATE TABLE mutation_trials (
    id TEXT PRIMARY KEY,
    parent_allele_id TEXT,
    child_allele_id TEXT,
    run_id TEXT NOT NULL,
    seed INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    fitness_before REAL,
    fitness_after REAL,
    stability_before REAL,
    stability_after REAL,
    accepted_parent_fitness REAL,
    delta REAL,
    parent_genome_hash TEXT,
    child_genome_hash TEXT,
    evaluation_result TEXT NOT NULL CHECK (
        evaluation_result IN (
            "PROMOTED",
            "REJECTED_FITNESS",
            "REJECTED_STABILITY",
            "REJECTED_GENERALIZATION",
            "REJECTED_THRESHOLD"
        )
    ),
    fitness_score REAL,
    generalization_score REAL,
    stability_score REAL,
    environment_small REAL,
    environment_medium REAL,
    environment_large REAL,
    combined_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES experiment_runs(id)
)
''')

# Recreate views
cursor.execute('''
CREATE VIEW IF NOT EXISTS promotion_audit AS
SELECT 
    mt.id as trial_id,
    mt.run_id,
    mt.seed,
    mt.generation,
    mt.fitness_before,
    mt.fitness_after,
    mt.delta,
    mt.accepted_parent_fitness,
    mt.evaluation_result,
    mt.fitness_score,
    mt.generalization_score,
    mt.stability_score,
    mt.environment_small,
    mt.environment_medium,
    mt.environment_large,
    mt.combined_score,
    me.parameter,
    me.mutation_type,
    me.mutation_order,
    me.old_value,
    me.new_value,
    me.attributed_delta
FROM mutation_trials mt
JOIN mutation_events me ON mt.id = me.trial_id
WHERE mt.evaluation_result = "PROMOTED"
''')

cursor.execute('''
CREATE VIEW IF NOT EXISTS gene_effects AS
SELECT
    me.parameter,
    COUNT(*) AS count,
    SUM(CASE WHEN me.attributed_delta > 0 THEN 1 ELSE 0 END) AS positive,
    SUM(CASE WHEN me.attributed_delta < 0 THEN 1 ELSE 0 END) AS negative,
    SUM(CASE WHEN me.attributed_delta = 0 THEN 1 ELSE 0 END) AS neutral,
    AVG(me.attributed_delta) AS avg_delta,
    SUM(me.attributed_delta) AS total_delta
FROM mutation_events me
GROUP BY me.parameter
''')

conn.commit()
print('✅ Database rebuilt with correct schema')
conn.close()
