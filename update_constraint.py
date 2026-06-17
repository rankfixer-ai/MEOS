import sqlite3
conn = sqlite3.connect('data/meos_v0.3.db')
cursor = conn.cursor()

# Create a new temporary table with the updated constraint
cursor.execute('''
CREATE TABLE mutation_trials_new (
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
            "ACCEPTED_EVOLUTION",
            "COMPENSATORY_STABILITY_PROMOTION",
            "REJECTED_FITNESS",
            "REJECTED_UNSTABLE",
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

# Copy data from old table
cursor.execute('''
INSERT INTO mutation_trials_new (
    id, parent_allele_id, child_allele_id, run_id, seed, generation,
    fitness_before, fitness_after, accepted_parent_fitness, delta,
    parent_genome_hash, child_genome_hash, evaluation_result,
    fitness_score, generalization_score, stability_score,
    environment_small, environment_medium, environment_large, created_at
)
SELECT 
    id, parent_allele_id, child_allele_id, run_id, seed, generation,
    fitness_before, fitness_after, accepted_parent_fitness, delta,
    parent_genome_hash, child_genome_hash, evaluation_result,
    fitness_score, generalization_score, stability_score,
    environment_small, environment_medium, environment_large, created_at
FROM mutation_trials
''')

# Drop old table and rename new one
cursor.execute('DROP TABLE mutation_trials')
cursor.execute('ALTER TABLE mutation_trials_new RENAME TO mutation_trials')

conn.commit()
print('✅ Updated CHECK constraint for evaluation_result')
conn.close()
