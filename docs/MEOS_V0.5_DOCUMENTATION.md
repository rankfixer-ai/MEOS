# MEOS V0.5 — Archive-Guided Evolutionary Optimization System

## Overview
MEOS is a deterministic, archive-guided evolutionary optimizer that mutates system configurations, measures performance against real metrics, and discovers optimal parameter settings through iterative selection, plateau recovery, and archive branching.

## Architecture

| Component | Status | Description |
|-----------|--------|-------------|
| P0: Determinism | ? | Same seed = same result. All bare random.* and salted hash() calls replaced |
| P2: Unfrozen genes | ? | Mutation options allow bidirectional parameter changes |
| P3: Switch logging | ? | Every active allele change logged with fitness transition |
| P4: Archive summary | ? | Post-run diversity and fitness distribution report |
| P5: Plateau strategy | ? | EXPLORE boost ? STAGNATION ? Archive branching with tabu list |
| Crossover | ? | Champion × archive parent recombination on stagnation |
| Tabu list | ? | Prevents immediate revisiting of recent branch targets |

## Performance (100-seed benchmark)

| Metric | Value |
|--------|-------|
| Mean fitness | 0.9729 |
| Median | 0.9735 |
| StdDev | 0.0041 |
| Max | 0.9793 |
| >0.97 rate | 81% |
| >0.95 rate | 100% |

## Key Discoveries

1. **Fitness ceiling is the benchmark, not the optimizer** — Every strategy (mutation, branching, crossover, single-env) converges to 0.978 ± 0.002
2. **Only 2 of 11 genome parameters are influential** — ranking_model_temp and scoring_strategy; the rest are frozen or low-impact
3. **The Pareto frontier is real** — Individual environments cap at ~0.978 even when optimized independently
4. **Archive branching produces genuine breakthroughs** — A 0.9549 side-branch found 0.9779, which the champion lineage couldn't reach

## Real-World Target: RisePinas Orchestrator

- Parameters: CYCLE_INTERVAL_MINUTES, SCRAPER_TIMEOUT_SECONDS, MAX_RETRIES
- Metrics: Supabase ? metrics_history table (ingestion, applications, alerts)
- Fitness: job freshness + data quality + alert accuracy
- Status: Live optimization in progress
