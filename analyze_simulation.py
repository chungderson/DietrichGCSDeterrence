"""
Analysis script for Deterrence Simulation

Runs the simulation multiple times and calculates statistical means for Round 1.
"""

import random
import sys
import os
from typing import Dict, List
from deterrence_simulation import DeterrenceSimulation, NUM_COUNTRIES


def run_single_simulation(seed: int = None, quiet: bool = True) -> Dict:
    """
    Run a single simulation and extract Round 1 statistics.
    
    Args:
        seed: Random seed for the simulation
        quiet: If True, suppress all print output
    
    Returns a dictionary with all relevant statistics.
    """
    # Suppress output if quiet mode
    if quiet:
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    
    try:
        # Create simulation with optional seed
        sim = DeterrenceSimulation(num_countries=NUM_COUNTRIES, seed=seed)
        
        # Store initial state
        initial_total = sim.get_total_value()
        initial_countries = sum(1 for c in sim.countries.values() if c.is_active)
        
        # Set previous values for the first round
        sim.previous_total_value = initial_total
        sim.previous_country_values = {
            c.id: c.private_value for c in sim.countries.values() if c.is_active
        }
        
        # Run one complete round-robin round
        results = sim.run_round()
        
        # Extract statistics
        round_end_total = sim.get_total_value()
        total_change = round_end_total - sim.round_start_total
        percentage_change = (total_change / sim.round_start_total * 100) if sim.round_start_total > 0 else 0
        
        # Count interactions
        bargains = sum(1 for r in results if r['outcome'] == 'bargain')
        attacks = sum(1 for r in results if r['outcome'] in ['attack_success', 'defense_success'])
        total_interactions = len(results)
        
        # Count attack outcomes
        attacks_successful = sum(1 for r in results if r['outcome'] == 'attack_success')
        attacks_failed = sum(1 for r in results if r['outcome'] == 'defense_success')
        
        # Count countries
        countries_at_start = sim.countries_at_start
        countries_at_end = sum(1 for c in sim.countries.values() if c.is_active)
        countries_eliminated = countries_at_start - countries_at_end
        
        # Aggregate country-level statistics
        total_attacks_attempted = sum(
            stats.get('attacks_attempted', 0) 
            for stats in sim.country_stats.values()
        )
        total_attacks_won = sum(
            stats.get('attacks_won', 0) 
            for stats in sim.country_stats.values()
        )
        total_attacks_lost = sum(
            stats.get('attacks_lost', 0) 
            for stats in sim.country_stats.values()
        )
        total_defended = sum(
            stats.get('defended', 0) 
            for stats in sim.country_stats.values()
        )
        
        # Calculate average growth rate
        growth_rates = list(sim.country_growth_rates.values())
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        result = {
            'initial_total_value': initial_total,
            'round_start_total': sim.round_start_total,
            'round_end_total': round_end_total,
            'total_value_change': total_change,
            'percentage_change': percentage_change,
            'initial_countries': initial_countries,
            'countries_at_start': countries_at_start,
            'countries_at_end': countries_at_end,
            'countries_eliminated': countries_eliminated,
            'bargains': bargains,
            'attacks': attacks,
            'attacks_successful': attacks_successful,
            'attacks_failed': attacks_failed,
            'total_interactions': total_interactions,
            'total_attacks_attempted': total_attacks_attempted,
            'total_attacks_won': total_attacks_won,
            'total_attacks_lost': total_attacks_lost,
            'total_defended': total_defended,
            'avg_growth_rate': avg_growth_rate,
        }
        
        return result
    finally:
        # Restore output if quiet mode
        if quiet:
            sys.stdout.close()
            sys.stdout = old_stdout


def calculate_statistics(data_list: List[Dict]) -> Dict:
    """
    Calculate mean, min, max, and standard deviation for each statistic.
    """
    if not data_list:
        return {}
    
    # Get all keys from first entry
    keys = data_list[0].keys()
    
    stats = {}
    for key in keys:
        values = [d[key] for d in data_list]
        mean = sum(values) / len(values)
        
        # Calculate standard deviation
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        stats[key] = {
            'mean': mean,
            'min': min(values),
            'max': max(values),
            'std_dev': std_dev,
        }
    
    return stats


def print_analysis_results(stats: Dict, num_runs: int):
    """
    Print formatted analysis results.
    """
    print("=" * 80)
    print(f"DETERRENCE SIMULATION ANALYSIS - {num_runs} RUNS")
    print("=" * 80)
    print()
    
    # Value Statistics
    print("VALUE STATISTICS")
    print("-" * 80)
    if 'initial_total_value' in stats:
        s = stats['initial_total_value']
        print(f"Initial Total Value:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.2f} | Max: {s['max']:.2f} | Std Dev: {s['std_dev']:.2f}")
    if 'round_start_total' in stats:
        s = stats['round_start_total']
        print(f"Round Start Total (after growth):")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.2f} | Max: {s['max']:.2f} | Std Dev: {s['std_dev']:.2f}")
    if 'round_end_total' in stats:
        s = stats['round_end_total']
        print(f"Round End Total:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.2f} | Max: {s['max']:.2f} | Std Dev: {s['std_dev']:.2f}")
    if 'total_value_change' in stats:
        s = stats['total_value_change']
        print(f"Total Value Change:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.2f} | Max: {s['max']:.2f} | Std Dev: {s['std_dev']:.2f}")
    if 'percentage_change' in stats:
        s = stats['percentage_change']
        print(f"Percentage Change:")
        print(f"  Mean: {s['mean']:+.2f}% | Min: {s['min']:+.2f}% | Max: {s['max']:+.2f}% | Std Dev: {s['std_dev']:.2f}%")
    print()
    
    # Country Statistics
    print("COUNTRY STATISTICS")
    print("-" * 80)
    if 'initial_countries' in stats:
        s = stats['initial_countries']
        print(f"Initial Countries:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'countries_at_start' in stats:
        s = stats['countries_at_start']
        print(f"Countries at Start of Round (after growth):")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'countries_at_end' in stats:
        s = stats['countries_at_end']
        print(f"Countries at End of Round:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'countries_eliminated' in stats:
        s = stats['countries_eliminated']
        print(f"Countries Eliminated:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'avg_growth_rate' in stats:
        s = stats['avg_growth_rate']
        print(f"Average Growth Rate:")
        print(f"  Mean: {s['mean']*100:.2f}% | Min: {s['min']*100:.2f}% | Max: {s['max']*100:.2f}% | Std Dev: {s['std_dev']*100:.2f}%")
    print()
    
    # Interaction Statistics
    print("INTERACTION STATISTICS")
    print("-" * 80)
    if 'total_interactions' in stats:
        s = stats['total_interactions']
        print(f"Total Interactions:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'bargains' in stats:
        s = stats['bargains']
        print(f"Bargains:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'attacks' in stats:
        s = stats['attacks']
        print(f"Total Attacks:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'attacks_successful' in stats:
        s = stats['attacks_successful']
        print(f"Successful Attacks:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'attacks_failed' in stats:
        s = stats['attacks_failed']
        print(f"Failed Attacks (Defense Successful):")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    print()
    
    # Attack Statistics (aggregated across all countries)
    print("AGGREGATE ATTACK STATISTICS (All Countries Combined)")
    print("-" * 80)
    if 'total_attacks_attempted' in stats:
        s = stats['total_attacks_attempted']
        print(f"Total Attacks Attempted:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'total_attacks_won' in stats:
        s = stats['total_attacks_won']
        print(f"Total Attacks Won:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'total_attacks_lost' in stats:
        s = stats['total_attacks_lost']
        print(f"Total Attacks Lost:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    if 'total_defended' in stats:
        s = stats['total_defended']
        print(f"Total Successful Defenses:")
        print(f"  Mean: {s['mean']:.2f} | Min: {s['min']:.0f} | Max: {s['max']:.0f} | Std Dev: {s['std_dev']:.2f}")
    print()
    
    # Calculate success rates
    if 'total_attacks_attempted' in stats and 'total_attacks_won' in stats:
        attempts_mean = stats['total_attacks_attempted']['mean']
        wins_mean = stats['total_attacks_won']['mean']
        if attempts_mean > 0:
            success_rate = (wins_mean / attempts_mean) * 100
            print(f"Attack Success Rate: {success_rate:.2f}%")
    print()
    
    print("=" * 80)


def main():
    """
    Main analysis function.
    """
    # Configuration
    NUM_RUNS = 100  # Number of simulation runs
    USE_RANDOM_SEEDS = True  # Use random seeds for each run
    
    print("Starting Analysis...")
    print(f"Running {NUM_RUNS} simulations...")
    print()
    
    # Collect data from all runs
    all_data = []
    
    for i in range(NUM_RUNS):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{NUM_RUNS} runs completed...")
        
        # Use random seed or sequential seed
        seed = random.randint(1, 1000000) if USE_RANDOM_SEEDS else i
        
        try:
            data = run_single_simulation(seed=seed)
            all_data.append(data)
        except Exception as e:
            print(f"Error in run {i + 1}: {e}")
            continue
    
    print(f"\nCompleted {len(all_data)} successful runs.")
    print()
    
    # Calculate statistics
    stats = calculate_statistics(all_data)
    
    # Print results
    print_analysis_results(stats, len(all_data))


if __name__ == "__main__":
    main()

