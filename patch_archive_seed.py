# Injecting Archive-Seed Logic
if self.no_improvement_counter >= 3 and self.elite_archive:
    # Use an elite genome instead of the active parent
    seed_genome = random.choice(self.elite_archive)["genome"]
    new_genome = self.mutation_engine.mutate(seed_genome, generation, current_fitness=self.active_fitness)
    print(f"[DEBUG] Stagnation detected at {self.active_fitness:.4f}. Seeding from Elite Archive.")
else:
    # Standard mutation
    new_genome = self.mutation_engine.mutate(self.active_genome, generation, current_fitness=self.active_fitness)
