filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# ============================================================
# P3: Archive switch logging in _set_active_allele
# ============================================================

old_set_active = '''def _set_active_allele(self, allele_id: str):
        self.db.execute("UPDATE alleles SET is_active = FALSE WHERE gene_id = (SELECT gene_id FROM alleles WHERE id = ?)", (allele_id,))
        self.db.execute("UPDATE alleles SET is_active = TRUE WHERE id = ?", (allele_id,))'''

new_set_active = '''def _set_active_allele(self, allele_id: str, reason: str = ""):
        old_active = self._get_active_allele()
        old_fitness = old_active["fitness_score"] if old_active else 0.0
        new_allele = self._get_allele(allele_id)
        new_fitness = new_allele["fitness_score"] if new_allele else 0.0
        self.db.execute("UPDATE alleles SET is_active = FALSE WHERE gene_id = (SELECT gene_id FROM alleles WHERE id = ?)", (allele_id,))
        self.db.execute("UPDATE alleles SET is_active = TRUE WHERE id = ?", (allele_id,))
        if old_active:
            print(f"   [SWITCH] {old_active['id'][:8]}->{allele_id[:8]} | {old_fitness:.4f}->{new_fitness:.4f} | {reason}")'''

c = c.replace(old_set_active, new_set_active)

# Update calls to _set_active_allele to include reason
c = c.replace(
    'self._set_active_allele(allele_id)',
    'self._set_active_allele(allele_id, "PROMOTED_CHAMPION" if evaluation_result == "PROMOTED_CHAMPION" else "PROMOTED" if evaluation_result == "PROMOTED" else "SOFT_PROMOTED" if evaluation_result == "PROMOTED_SOFT" else evaluation_result)'
)

# ============================================================
# P4: Archive diversity measurement (every 10 gens)
# ============================================================

old_gen10 = '''if gen % 10 == 0:
                print(f"   Gen {gen:3d}: {status} Fitness: {fitness_score:.3f} "
                      f"(Delta: {delta_fitness:+.3f}) Active: {parent_fitness:.3f} "
                      f"Stability: {stability_score:.3f} | Result: {evaluation_result}")'''

new_gen10 = '''if gen % 10 == 0:
                print(f"   Gen {gen:3d}: {status} Fitness: {fitness_score:.3f} "
                      f"(Delta: {delta_fitness:+.3f}) Active: {parent_fitness:.3f} "
                      f"Stability: {stability_score:.3f} | Result: {evaluation_result}")
                # P4: Archive diversity check
                top_alleles = self.db.execute(
                    "SELECT fitness_score, stability_score, genome FROM alleles WHERE gene_id = ? AND fitness_score IS NOT NULL ORDER BY fitness_score DESC LIMIT 10",
                    (self.gene_id,)
                )
                if len(top_alleles) >= 3:
                    fitnesses = [float(a[0]) for a in top_alleles if a[0] is not None]
                    if max(fitnesses) - min(fitnesses) < 0.005:
                        print(f"   [ARCHIVE] Low diversity: top10 spread={max(fitnesses)-min(fitnesses):.4f}")'''

c = c.replace(old_gen10, new_gen10)

with open(filepath, 'w') as f:
    f.write(c)

print('P3 + P4 applied:')
print('  - _set_active_allele now logs every switch with old->new fitness')
print('  - Every 10 gens: archive diversity check (alerts if spread < 0.005)')
