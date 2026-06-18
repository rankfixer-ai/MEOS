# MEOS V0.5 — Archive-Guided Evolutionary Optimization System

## Overview

MEOS is a deterministic, archive-guided evolutionary optimizer that discovers optimal system configurations through mutation, benchmarking, and iterative selection. It preserves champion genomes, detects plateaus, and escapes local optima through archive branching and crossover.

**Current verified max fitness: 0.9793** (81% of seeds exceed 0.97 across 100-seed benchmark)

## What's New Since V0.3

| Feature | Status | Description |
|---------|--------|-------------|
| Full determinism | ? | Same seed = identical trajectory |
| Archive branching | ? | Switches to archived allele on stagnation |
| Tabu list | ? | Prevents immediate revisiting of recent branches |
| Crossover | ? | Champion x archive parent recombination |
| Switch logging | ? | Every allele change logged with fitness |
| Archive summary | ? | Post-run diversity report |
| Reranking unfrozen | ? | Parameter can toggle both directions |

## Performance (100-Seed Benchmark)

| Metric | V0.3 | V0.5 |
|--------|------|------|
| Best single run | 0.9640 | 0.9793 |
| Mean | ~0.96 | 0.9729 |
| Median | - | 0.9735 |
| StdDev | - | 0.0041 |
| >0.97 rate | 0% | 81% |
| >0.95 rate | ~60% | 100% |

## Key Discoveries

1. Fitness ceiling is the benchmark, not the optimizer
2. Only 2 of 11 parameters are influential
3. Archive branching produces genuine breakthroughs
4. 100% of seeds reach >0.95

## Real-World Target

Currently optimizing RisePinas orchestrator via live Supabase telemetry.
