"""
MEOS V0.3 - Root Entry Point
CLI Gateway for the Evolutionary Engine
"""

import sys
import argparse
from src.selection.selection_engine import SelectionEngine
from src.core.meos_v0_3_core import run_evolutionary_loop

print("STEP 0: File loaded")
print("STEP 1: About to import sys")

def main():
    print("STEP 3: Entered main()")
    
    print("STEP 3.2: Creating parser")
    parser = argparse.ArgumentParser(description="MEOS V0.3 - Explainable Evolution Engine")
    
    print("STEP 3.3: Adding arguments")
    parser.add_argument("--seed", type=int, default=42, help="Random number generator seed")
    parser.add_argument("--generations", type=int, default=50, help="Maximum evolution cycles")
    parser.add_argument("--threshold", type=float, default=0.89, help="Generalization fitness target")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--seed_genome", type=str, default=None, help="JSON genome to seed the run")
    
    print("STEP 3.4: Parsing args")
    args = parser.parse_args()
    print(f"STEP 3.5: Args parsed - seed={args.seed}")

    print("STEP 4: Creating selector")
    selector = SelectionEngine(target_threshold=args.threshold)

    print("STEP 5: Calling run_evolutionary_loop")
    run_evolutionary_loop(args.seed, args.generations, selector, seed_genome=args.seed_genome, debug=args.debug)
    print("STEP 6: run_evolutionary_loop returned")

if __name__ == "__main__":
    main()

