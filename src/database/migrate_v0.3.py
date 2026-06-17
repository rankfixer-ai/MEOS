"""
MEOS V0.3 - Database Migration
Adds mutation_trials, mutation_events, experiment_runs tables.
"""

import sqlite3
import os

def migrate():
    db_path = "data/meos_v0.3.db"
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, f"{db_path}.backup")
        print(f"📦 Backed up existing database to {db_path}.backup")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # === experiment_runs ===
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiment_runs (
            id TEXT PRIMARY KEY,
            seed INTEGER NOT NULL,
            baseline_fitness REAL,
            final_fitness REAL,
            success INTEGER DEFAULT 0,
            plateau_generation INTEGER,
            total_generations INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # === mutation_trials ===
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutation_trials (
            id TEXT PRIMARY KEY,
            parent_allele_id TEXT,
            child_allele_id TEXT,
            run_id TEXT NOT NULL,
            seed INTEGER NOT NULL,
            generation INTEGER NOT NULL,
            fitness_before REAL,
            fitness_after REAL,
            accepted_parent_fitness REAL,
            delta REAL,
            parent_genome_hash TEXT,
            child_genome_hash TEXT,
            evaluation_result TEXT NOT NULL CHECK (
                evaluation_result IN (
                    'PROMOTED',
                    'REJECTED_FITNESS',
                    'REJECTED_STABILITY',
                    'REJECTED_GENERALIZATION',
                    'REJECTED_THRESHOLD'
                )
            ),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES experiment_runs(id)
        )
    ''')
    
    # === mutation_events ===
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutation_events (
            id TEXT PRIMARY KEY,
            trial_id TEXT NOT NULL,
            parameter TEXT NOT NULL,
            mutation_type TEXT NOT NULL CHECK (
                mutation_type IN (
                    'toggle_boolean',
                    'increase_numeric',
                    'decrease_numeric',
                    'categorical_swap'
                )
            ),
            mutation_order INTEGER NOT NULL,
            old_value TEXT,
            new_value TEXT,
            FOREIGN KEY (trial_id) REFERENCES mutation_trials(id)
        )
    ''')
    
    # === promotion_audit view ===
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
            me.parameter,
            me.mutation_type,
            me.mutation_order,
            me.old_value,
            me.new_value
        FROM mutation_trials mt
        JOIN mutation_events me ON mt.id = me.trial_id
        WHERE mt.evaluation_result = 'PROMOTED'
    ''')
    
    # === Indexes ===
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_run ON mutation_trials(run_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_generation ON mutation_trials(seed, generation)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trials_result ON mutation_trials(evaluation_result)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_trial ON mutation_events(trial_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_parameter ON mutation_events(parameter)')
    
    # === Unique constraint for hash collision detection ===
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_hash_unique
        ON mutation_trials(parent_genome_hash, child_genome_hash, generation, seed)
    ''')
    
    conn.commit()
    
    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")
    tables = cursor.fetchall()
    print("\n📊 Created tables and views:")
    for table in tables:
        print(f"  ✅ {table[0]}")
    
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()