"""
Visualization script for Deterrence Simulation

Creates various visualizations to understand deterrence dynamics.
"""

import sys
import os
from typing import Dict, List, Tuple
from collections import defaultdict

# Check for required dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    import seaborn as sns
except ImportError as e:
    print("=" * 60)
    print("ERROR: Missing required dependencies")
    print("=" * 60)
    print("\nPlease install the required packages by running:")
    print("  pip install -r requirements.txt")
    print("\nOr install individually:")
    print("  pip install matplotlib seaborn numpy")
    print("\nIf you're using a virtual environment, make sure it's activated.")
    print("=" * 60)
    sys.exit(1)

# Import simulation
from deterrence_simulation import DeterrenceSimulation, NUM_COUNTRIES

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def run_multi_round_simulation(num_rounds: int = 5, seed: int = None) -> Dict:
    """
    Run simulation for multiple rounds and collect data.
    
    Returns dictionary with:
    - rounds: list of round data
    - country_history: dict of country_id -> list of values over rounds
    - interaction_history: list of all interactions across rounds
    """
    sim = DeterrenceSimulation(num_countries=NUM_COUNTRIES, seed=seed)
    
    # Suppress output
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        # Initialize
        initial_total = sim.get_total_value()
        sim.previous_total_value = initial_total
        sim.previous_country_values = {
            c.id: c.private_value for c in sim.countries.values() if c.is_active
        }
        
        rounds_data = []
        country_history = defaultdict(list)
        interaction_history = []
        
        # Track initial values
        for country_id, country in sim.countries.items():
            country_history[country_id].append({
                'value': country.private_value,
                'is_active': country.is_active,
                'round': 0
            })
        
        # Run rounds
        for round_num in range(1, num_rounds + 1):
            results = sim.run_round()
            
            # Pre-calculate counters
            total_value = sim.get_total_value()
            active_countries = sum(1 for c in sim.countries.values() if c.is_active)
            bargains_count = sum(1 for r in results if r['outcome'] == 'bargain')
            attacks_count = sum(1 for r in results if r['outcome'] in ['attack_success', 'defense_success'])
            attacks_successful = sum(1 for r in results if r['outcome'] == 'attack_success')
            attacks_failed = sum(1 for r in results if r['outcome'] == 'defense_success')
            
            # Estimate value preserved by bargaining (negative EV avoided)
            value_saved_by_bargains = 0.0
            
            # Track country values
            for country_id, country in sim.countries.items():
                country_history[country_id].append({
                    'value': country.private_value if country.is_active else 0,
                    'is_active': country.is_active,
                    'round': round_num
                })
            
            # Collect interactions
            for result in results:
                if result['outcome'] == 'bargain':
                    saved1 = max(-(result.get('country1_ev_attack_actual', 0.0) or 0.0), 0.0)
                    saved2 = max(-(result.get('country2_ev_attack_actual', 0.0) or 0.0), 0.0)
                    value_saved_by_bargains += saved1 + saved2
                
                interaction_history.append({
                    'round': round_num,
                    **result
                })
            
            # Collect round statistics (including deterrence savings)
            round_stats = {
                'round': round_num,
                'total_value': total_value,
                'active_countries': active_countries,
                'bargains': bargains_count,
                'attacks': attacks_count,
                'attacks_successful': attacks_successful,
                'attacks_failed': attacks_failed,
                'value_saved_by_bargains': value_saved_by_bargains,
                'attacks_prevented': bargains_count,
            }
            rounds_data.append(round_stats)
        
        sys.stdout.close()
        sys.stdout = old_stdout
        
        return {
            'rounds': rounds_data,
            'country_history': dict(country_history),
            'interactions': interaction_history,
            'initial_total': initial_total
        }
    except Exception as e:
        sys.stdout.close()
        sys.stdout = old_stdout
        raise e


def plot_attack_vs_bargain_rate(rounds_data: List[Dict], save_path: str = None):
    """Plot 1: Attack rate vs Bargain rate over time"""
    rounds = [r['round'] for r in rounds_data]
    attacks = [r['attacks'] for r in rounds_data]
    bargains = [r['bargains'] for r in rounds_data]
    total_interactions = [a + b for a, b in zip(attacks, bargains)]
    
    attack_rate = [a / t * 100 if t > 0 else 0 for a, t in zip(attacks, total_interactions)]
    bargain_rate = [b / t * 100 if t > 0 else 0 for b, t in zip(bargains, total_interactions)]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rounds, attack_rate, 'r-o', label='Attack Rate', linewidth=2, markersize=8)
    ax.plot(rounds, bargain_rate, 'g-s', label='Bargain Rate (Deterred)', linewidth=2, markersize=8)
    ax.fill_between(rounds, 0, attack_rate, alpha=0.3, color='red')
    ax.fill_between(rounds, attack_rate, [100]*len(rounds), alpha=0.3, color='green')
    
    ax.set_xlabel('Round', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage of Interactions (%)', fontsize=12, fontweight='bold')
    ax.set_title('Deterrence Effectiveness: Attack Rate vs Bargain Rate Over Time', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_perceived_vs_actual_ev(interactions: List[Dict], save_path: str = None):
    """Plot 2: Perceived EV vs Actual EV scatter plot"""
    # Extract data
    perceived_evs = []
    actual_evs = []
    actions = []
    colors = []
    
    for interaction in interactions:
        if 'country1_ev_attack_perceived' in interaction:
            perceived_evs.append(interaction['country1_ev_attack_perceived'])
            actual_evs.append(interaction['country1_ev_attack_actual'])
            actions.append(interaction.get('action1', 'unknown'))
            colors.append('red' if interaction.get('action1') == 'attack' else 'blue')
        
        if 'country2_ev_attack_perceived' in interaction:
            perceived_evs.append(interaction['country2_ev_attack_perceived'])
            actual_evs.append(interaction['country2_ev_attack_actual'])
            actions.append(interaction.get('action2', 'unknown'))
            colors.append('red' if interaction.get('action2') == 'attack' else 'blue')
    
    if not perceived_evs:
        print("No EV data available for visualization")
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create scatter plot
    attack_mask = [c == 'red' for c in colors]
    bargain_mask = [c == 'blue' for c in colors]
    
    if any(attack_mask):
        ax.scatter([p for i, p in enumerate(perceived_evs) if attack_mask[i]],
                  [a for i, a in enumerate(actual_evs) if attack_mask[i]],
                  c='red', alpha=0.6, s=50, label='Chose Attack', edgecolors='darkred', linewidth=0.5)
    
    if any(bargain_mask):
        ax.scatter([p for i, p in enumerate(perceived_evs) if bargain_mask[i]],
                  [a for i, a in enumerate(actual_evs) if bargain_mask[i]],
                  c='blue', alpha=0.6, s=50, label='Chose Bargain (Deterred)', edgecolors='darkblue', linewidth=0.5)
    
    # Add diagonal line (perfect perception)
    min_val = min(min(perceived_evs), min(actual_evs))
    max_val = max(max(perceived_evs), max(actual_evs))
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=1, label='Perfect Perception')
    
    # Add zero lines
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    ax.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Perceived EV of Attack', fontsize=12, fontweight='bold')
    ax.set_ylabel('Actual EV of Attack', fontsize=12, fontweight='bold')
    ax.set_title('Perception vs Reality: How Misperception Affects Deterrence Decisions',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_country_survival(country_history: Dict, save_path: str = None):
    """Plot 3: Country survival over time"""
    max_rounds = max(len(history) for history in country_history.values())
    rounds = list(range(max_rounds))
    
    # Count active countries per round
    active_counts = []
    for round_num in range(max_rounds):
        active = sum(1 for history in country_history.values() 
                    if round_num < len(history) and history[round_num]['is_active'])
        active_counts.append(active)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rounds, active_counts, 'b-o', linewidth=2, markersize=8, label='Active Countries')
    ax.fill_between(rounds, 0, active_counts, alpha=0.3, color='blue')
    
    ax.set_xlabel('Round', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Active Countries', fontsize=12, fontweight='bold')
    ax.set_title('Country Survival: Impact of Deterrence on System Stability',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_total_value_over_time(rounds_data: List[Dict], initial_total: float, save_path: str = None):
    """Plot 4: Total system value over time"""
    rounds = [0] + [r['round'] for r in rounds_data]
    values = [initial_total] + [r['total_value'] for r in rounds_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rounds, values, 'g-o', linewidth=2, markersize=8, label='Total System Value')
    ax.fill_between(rounds, 0, values, alpha=0.3, color='green')
    
    # Add percentage change annotations
    for i, r in enumerate(rounds_data):
        if i > 0:
            prev_value = values[i]
            curr_value = values[i+1]
            pct_change = ((curr_value - prev_value) / prev_value * 100) if prev_value > 0 else 0
            if abs(pct_change) > 1:  # Only annotate significant changes
                ax.annotate(f'{pct_change:+.1f}%', 
                           xy=(r['round'], curr_value),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, alpha=0.7)
    
    ax.set_xlabel('Round', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total System Value', fontsize=12, fontweight='bold')
    ax.set_title('System Value Preservation: How Deterrence Affects Total Wealth',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_attack_success_rate(rounds_data: List[Dict], save_path: str = None):
    """Plot 5: Attack success rate over time"""
    rounds = [r['round'] for r in rounds_data]
    successful = [r['attacks_successful'] for r in rounds_data]
    total_attacks = [r['attacks'] for r in rounds_data]
    
    success_rates = [s / t * 100 if t > 0 else 0 for s, t in zip(successful, total_attacks)]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rounds, success_rates, 'orange', marker='o', linewidth=2, markersize=8, label='Attack Success Rate')
    ax.fill_between(rounds, 0, success_rates, alpha=0.3, color='orange')
    
    # Add horizontal line at 50% for reference
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50% Reference')
    
    ax.set_xlabel('Round', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Attack Success Rate: Effectiveness of Defense Over Time',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_ev_comparison(interactions: List[Dict], save_path: str = None):
    """Plot 6: Comparison of Perceived EV, Actual EV, and Bargain EV"""
    # Sample a subset of interactions for clarity
    sample_size = min(50, len(interactions))
    sampled = np.random.choice(len(interactions), sample_size, replace=False)
    
    perceived_ev_attack = []
    actual_ev_attack = []
    ev_bargain = []
    actions = []
    
    for idx in sampled:
        interaction = interactions[idx]
        if 'country1_ev_attack_perceived' in interaction:
            perceived_ev_attack.append(interaction['country1_ev_attack_perceived'])
            actual_ev_attack.append(interaction['country1_ev_attack_actual'])
            ev_bargain.append(interaction.get('country1_ev_bargain', 0))
            actions.append(interaction.get('action1', 'unknown'))
    
    if not perceived_ev_attack:
        print("No EV data available for visualization")
        return
    
    x = np.arange(len(perceived_ev_attack))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    bars1 = ax.bar(x - width, perceived_ev_attack, width, label='Perceived EV (Attack)', 
                   color='red', alpha=0.7)
    bars2 = ax.bar(x, actual_ev_attack, width, label='Actual EV (Attack)', 
                   color='orange', alpha=0.7)
    bars3 = ax.bar(x + width, ev_bargain, width, label='EV (Bargain)', 
                   color='green', alpha=0.7)
    
    # Color code by action
    for i, action in enumerate(actions):
        if action == 'attack':
            bars1[i].set_edgecolor('darkred')
            bars1[i].set_linewidth(2)
    
    ax.set_xlabel('Interaction Index (Sampled)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Expected Value', fontsize=12, fontweight='bold')
    ax.set_title('Expected Value Comparison: Why Countries Choose Attack vs Bargain',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_bargain_value_saved(rounds_data: List[Dict], save_path: str = None):
    """Plot 7: Value saved by bargaining (deterrence impact)"""
    if not rounds_data:
        print("No round data available for bargain value visualization")
        return
    
    rounds = [r['round'] for r in rounds_data]
    saved_values = [r.get('value_saved_by_bargains', 0.0) for r in rounds_data]
    
    cumulative_saved = []
    running_total = 0.0
    for value in saved_values:
        running_total += value
        cumulative_saved.append(running_total)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    bars = ax1.bar(rounds, saved_values, color='#2E8B57', alpha=0.75, label='Value preserved this round')
    ax1.set_xlabel('Round', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Value preserved (one round)', color='#2E8B57', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#2E8B57')
    
    # Add cumulative line
    ax2 = ax1.twinx()
    ax2.plot(rounds, cumulative_saved, color='#004225', linewidth=2.5, marker='o', label='Cumulative value preserved')
    ax2.set_ylabel('Cumulative value preserved', color='#004225', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#004225')
    
    # Combine legends
    handles = [bars] + ax2.lines
    labels = ['Value preserved this round', 'Cumulative value preserved']
    ax1.legend(handles, labels, loc='upper left', fontsize=10)
    
    ax1.set_title('Bargaining Payoff: Value Preserved by Avoiding Costly Wars', fontsize=14, fontweight='bold')
    ax1.grid(True, axis='y', alpha=0.2)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def create_deterrence_dashboard(simulation_data: Dict, output_dir: str = "visualizations"):
    """Create all visualizations in a dashboard format"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("Creating deterrence visualizations...")
    
    # Plot 1: Attack vs Bargain Rate
    print("  - Attack vs Bargain Rate")
    plot_attack_vs_bargain_rate(simulation_data['rounds'], 
                               save_path=f"{output_dir}/1_attack_vs_bargain_rate.png")
    
    # Plot 1b: Value saved by bargains
    print("  - Value Saved by Bargains")
    plot_bargain_value_saved(simulation_data['rounds'],
                             save_path=f"{output_dir}/1b_bargain_value_saved.png")
    
    # Plot 2: Perceived vs Actual EV
    print("  - Perceived vs Actual EV")
    plot_perceived_vs_actual_ev(simulation_data['interactions'],
                               save_path=f"{output_dir}/2_perceived_vs_actual_ev.png")
    
    # Plot 3: Country Survival
    print("  - Country Survival")
    plot_country_survival(simulation_data['country_history'],
                         save_path=f"{output_dir}/3_country_survival.png")
    
    # Plot 4: Total Value Over Time
    print("  - Total Value Over Time")
    plot_total_value_over_time(simulation_data['rounds'], 
                               simulation_data['initial_total'],
                               save_path=f"{output_dir}/4_total_value_over_time.png")
    
    # Plot 5: Attack Success Rate
    print("  - Attack Success Rate")
    plot_attack_success_rate(simulation_data['rounds'],
                            save_path=f"{output_dir}/5_attack_success_rate.png")
    
    # Plot 6: EV Comparison
    print("  - EV Comparison")
    plot_ev_comparison(simulation_data['interactions'],
                      save_path=f"{output_dir}/6_ev_comparison.png")
    
    print(f"\nAll visualizations saved to '{output_dir}/' directory")


def main():
    """Main function to run visualization"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize deterrence simulation dynamics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_deterrence.py              # Run 1 round (default, matches main simulation)
  python visualize_deterrence.py --rounds 5  # Run 5 rounds to see trends
  python visualize_deterrence.py --rounds 10 --seed 123  # Run 10 rounds with specific seed
        """
    )
    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=1,
        help='Number of rounds to simulate (default: 1, matches main simulation)'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='visualizations',
        help='Output directory for visualization files (default: visualizations)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DETERRENCE SIMULATION VISUALIZATION")
    print("=" * 60)
    print()
    
    print(f"Configuration:")
    print(f"  - Rounds: {args.rounds}")
    print(f"  - Seed: {args.seed}")
    print(f"  - Output directory: {args.output_dir}")
    print()
    
    print(f"Running simulation for {args.rounds} round(s)...")
    simulation_data = run_multi_round_simulation(num_rounds=args.rounds, seed=args.seed)
    
    print(f"Simulation complete!")
    print(f"  - Total interactions: {len(simulation_data['interactions'])}")
    print(f"  - Rounds: {len(simulation_data['rounds'])}")
    
    total_bargains = sum(r.get('bargains', 0) for r in simulation_data['rounds'])
    total_value_saved = sum(r.get('value_saved_by_bargains', 0.0) for r in simulation_data['rounds'])
    total_interactions = sum((r.get('bargains', 0) + r.get('attacks', 0)) for r in simulation_data['rounds'])
    
    if total_interactions > 0:
        print(f"  - Bargains: {total_bargains} ({(total_bargains/total_interactions)*100:.1f}% of interactions)")
    else:
        print(f"  - Bargains: {total_bargains}")
    print(f"  - Estimated value preserved by bargaining: {total_value_saved:,.2f}")
    print()
    
    # Create visualizations
    create_deterrence_dashboard(simulation_data, output_dir=args.output_dir)
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

