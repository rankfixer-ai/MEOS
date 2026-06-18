filepath = r'src\core\meos_v0_3_core.py'
with open(filepath, 'r') as f:
    c = f.read()

# Fix 1: Use hash of genome JSON + env for engine seed (full genome, not just parallelism)
old = "engine = SearchEngine(genome, seed=hash(str(genome.get(\"parallelism\",1)) + env_name) % 10000)"
new = "engine = SearchEngine(genome, seed=hash(json.dumps(genome, sort_keys=True) + env_name) % 10000)"
c = c.replace(old, new)

# Fix 2: Use seeded RNG per benchmark call instead of hardcoded 42
# Pass a seed derived from the generation into _generate_queries
old_sig = 'def run_multi_env_benchmark(self, allele_id: str, genome: Dict) -> Dict:'
new_sig = 'def run_multi_env_benchmark(self, allele_id: str, genome: Dict, gen_seed: int = 42) -> Dict:'
c = c.replace(old_sig, new_sig)

# Use gen_seed in query generation
old_qcall = 'queries = self._generate_queries(env_config["queries"], env_config["sources"])'
new_qcall = 'queries = self._generate_queries(env_config["queries"], env_config["sources"], gen_seed + env_index)'
# Need to add env_index to the loop
old_loop = 'for env_name, env_config in ENVIRONMENTS.items():'
new_loop = 'for env_index, (env_name, env_config) in enumerate(ENVIRONMENTS.items()):'
c = c.replace(old_loop, new_loop)
c = c.replace(old_qcall, new_qcall)

# Update _generate_queries signature
old_gsig = 'def _generate_queries(self, count: int, sources_per_query: int) -> List[Dict]:'
new_gsig = 'def _generate_queries(self, count: int, sources_per_query: int, seed: int = 42) -> List[Dict]:'
c = c.replace(old_gsig, new_gsig)

# Use the passed seed instead of hardcoded 42
c = c.replace("random.Random(42).sample", "random.Random(seed).sample")
c = c.replace("random.Random(42).choice", "random.Random(seed).choice")

# Pass gen to benchmark calls
old_call1 = "results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome)"
new_call1 = "results = self.benchmark_runner.run_multi_env_benchmark(allele_id, new_genome, gen)"
c = c.replace(old_call1, new_call1)

old_call2 = "results = benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome)"
new_call2 = "results = benchmark_runner.run_multi_env_benchmark(allele_id, initial_genome, 0)"
c = c.replace(old_call2, new_call2)

with open(filepath, 'w') as f:
    f.write(c)
print('Parameterized seed: each generation gets deterministic-but-different evaluation')
