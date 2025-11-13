"""
Deterrence Modeling Simulation

This simulation demonstrates the concept of deterrence through a bargaining model
where countries can choose to attack or bargain with each other.
"""

import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Country:
    """Represents a country in the simulation."""
    id: int
    private_value: float
    perceived_values: Dict[int, float] = field(default_factory=dict)
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize perceived values for all other countries."""
        if not self.perceived_values:
            # Perceived values will be set during initialization
            pass
    
    def get_perceived_odds(self, other_id: int, all_countries: Dict[int, 'Country']) -> float:
        """
        Calculate perceived odds of winning against another country.
        Formula: (private_value + perceived_value_of_other) / (total sum of perceived values)
        Total sum includes: self's private value + self's perceived value of other + 
                           other's private value + other's perceived value of self
        """
        other_country = all_countries.get(other_id)
        if not other_country:
            return 0.5
        
        # This country's contribution to the total
        self_contribution = self.private_value + self.perceived_values.get(other_id, 0)
        
        # Other country's contribution to the total
        other_contribution = other_country.private_value + other_country.perceived_values.get(self.id, 0)
        
        # Total sum of perceived values
        total = self_contribution + other_contribution
        
        if total == 0:
            return 0.5  # Default to 50/50 if no values
        
        return self_contribution / total
    
    def get_attack_cost(self, other_id: int, all_countries: Dict[int, 'Country']) -> float:
        """Calculate the cost of attack (10% of total perceived values)."""
        other_country = all_countries.get(other_id)
        if not other_country:
            return 0
        
        # Total sum of perceived values (same as in get_perceived_odds)
        self_contribution = self.private_value + self.perceived_values.get(other_id, 0)
        other_contribution = other_country.private_value + other_country.perceived_values.get(self.id, 0)
        total = self_contribution + other_contribution
        
        return total * 0.10
    
    def decide_action(self, other_id: int, all_countries: Dict[int, 'Country']) -> str:
        """
        Decide whether to attack or bargain.
        For now, uses a simple strategy: attack if perceived odds > 0.6 and cost is acceptable.
        """
        odds = self.get_perceived_odds(other_id, all_countries)
        cost = self.get_attack_cost(other_id, all_countries)
        
        # Simple strategy: attack if odds are favorable and cost is less than potential gain
        if odds > 0.6 and cost < self.private_value * 0.3:
            return "attack"
        else:
            return "bargain"


class DeterrenceSimulation:
    """Main simulation class for the deterrence model."""
    
    def __init__(self, num_countries: int = 10, seed: Optional[int] = None):
        """Initialize the simulation with specified number of countries."""
        if seed is not None:
            random.seed(seed)
        
        self.num_countries = num_countries
        self.countries: Dict[int, Country] = {}
        self.round_number = 0
        self.era = 1  # Track which era we're in
        
        self._initialize_countries()
    
    def _initialize_countries(self):
        """Initialize all countries with random private values and perceived values."""
        # Generate private values (100-1000)
        private_values = {}
        for i in range(1, self.num_countries + 1):
            private_values[i] = random.uniform(100, 1000)
        
        # Create countries and set perceived values
        for i in range(1, self.num_countries + 1):
            perceived_values = {}
            for j in range(1, self.num_countries + 1):
                if i != j:
                    # Perceived value is within 15% of the other country's private value
                    base_value = private_values[j]
                    perceived_values[j] = random.uniform(
                        base_value * 0.85,
                        base_value * 1.15
                    )
            
            self.countries[i] = Country(
                id=i,
                private_value=private_values[i],
                perceived_values=perceived_values
            )
    
    def _update_perceived_values(self, country1_id: int, country2_id: int):
        """
        Update all other countries' perceived values of country1 and country2
        within 15% of their true private values.
        """
        country1 = self.countries[country1_id]
        country2 = self.countries[country2_id]
        
        for other_id, other_country in self.countries.items():
            if other_id not in [country1_id, country2_id] and other_country.is_active:
                # Update perception of country1
                if country1_id in other_country.perceived_values:
                    true_value = country1.private_value
                    other_country.perceived_values[country1_id] = random.uniform(
                        true_value * 0.85,
                        true_value * 1.15
                    )
                
                # Update perception of country2
                if country2_id in other_country.perceived_values:
                    true_value = country2.private_value
                    other_country.perceived_values[country2_id] = random.uniform(
                        true_value * 0.85,
                        true_value * 1.15
                    )
    
    def _resolve_attack(self, attacker_id: int, defender_id: int) -> Tuple[str, Dict]:
        """
        Resolve an attack between two countries.
        Returns: (outcome, details_dict)
        """
        attacker = self.countries[attacker_id]
        defender = self.countries[defender_id]
        
        # Calculate perceived odds for attacker
        attacker_odds = attacker.get_perceived_odds(defender_id, self.countries)
        
        # Determine actual outcome based on odds
        attack_succeeds = random.random() < attacker_odds
        cost = attacker.get_attack_cost(defender_id, self.countries)
        
        if attack_succeeds:
            # Attacker wins: gets all defender's value, then cost is imposed
            attacker.private_value += defender.private_value
            attacker.private_value -= cost
            
            # Remove defender from game
            defender.is_active = False
            
            # Update perceived values for all other countries
            self._update_perceived_values(attacker_id, defender_id)
            
            return "attack_success", {
                "attacker": attacker_id,
                "defender": defender_id,
                "attacker_new_value": attacker.private_value,
                "defender_removed": True
            }
        else:
            # Defense successful: both lose 10% of their value
            attacker.private_value *= 0.9
            defender.private_value *= 0.9
            
            # Update perceived values for all other countries
            self._update_perceived_values(attacker_id, defender_id)
            
            return "defense_success", {
                "attacker": attacker_id,
                "defender": defender_id,
                "attacker_new_value": attacker.private_value,
                "defender_new_value": defender.private_value
            }
    
    def _resolve_bargain(self, country1_id: int, country2_id: int) -> Dict:
        """
        Resolve a bargain between two countries.
        Both gain 5% of their private value.
        """
        country1 = self.countries[country1_id]
        country2 = self.countries[country2_id]
        
        gain1 = country1.private_value * 0.05
        gain2 = country2.private_value * 0.05
        
        country1.private_value += gain1
        country2.private_value += gain2
        
        # Update perceived values for all other countries
        self._update_perceived_values(country1_id, country2_id)
        
        return {
            "country1": country1_id,
            "country2": country2_id,
            "country1_new_value": country1.private_value,
            "country2_new_value": country2.private_value,
            "country1_gain": gain1,
            "country2_gain": gain2
        }
    
    def _get_first_era_pairs(self) -> List[Tuple[int, int]]:
        """Get pairs for the first era: (1,2), (3,4), (5,6), (7,8), (9,10)."""
        pairs = []
        active_countries = sorted([c.id for c in self.countries.values() if c.is_active])
        
        for i in range(0, len(active_countries) - 1, 2):
            pairs.append((active_countries[i], active_countries[i + 1]))
        
        return pairs
    
    def _get_round_robin_pairs(self) -> List[Tuple[int, int]]:
        """Get all pairs for round-robin format."""
        active_countries = sorted([c.id for c in self.countries.values() if c.is_active])
        pairs = []
        
        for i in range(len(active_countries)):
            for j in range(i + 1, len(active_countries)):
                pairs.append((active_countries[i], active_countries[j]))
        
        return pairs
    
    def run_round(self) -> List[Dict]:
        """Run a single round of the simulation."""
        self.round_number += 1
        results = []
        
        # Determine pairs based on era
        if self.era == 1:
            pairs = self._get_first_era_pairs()
            self.era = 2  # Switch to round-robin after first era
        else:
            pairs = self._get_round_robin_pairs()
        
        # Process each pair
        for country1_id, country2_id in pairs:
            country1 = self.countries[country1_id]
            country2 = self.countries[country2_id]
            
            if not country1.is_active or not country2.is_active:
                continue
            
            # Each country decides their action
            action1 = country1.decide_action(country2_id, self.countries)
            action2 = country2.decide_action(country1_id, self.countries)
            
            # Resolve the interaction
            if action1 == "attack" and action2 == "attack":
                # Both attack - resolve as mutual attack (attacker1 attacks first)
                outcome, details = self._resolve_attack(country1_id, country2_id)
                results.append({
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    **details
                })
            elif action1 == "attack":
                # Country1 attacks, country2 defends
                outcome, details = self._resolve_attack(country1_id, country2_id)
                results.append({
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    **details
                })
            elif action2 == "attack":
                # Country2 attacks, country1 defends
                outcome, details = self._resolve_attack(country2_id, country1_id)
                results.append({
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    **details
                })
            else:
                # Both bargain
                details = self._resolve_bargain(country1_id, country2_id)
                results.append({
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "action1": action1,
                    "action2": action2,
                    "outcome": "bargain",
                    **details
                })
        
        return results
    
    def get_status(self) -> Dict:
        """Get current status of all countries."""
        return {
            "round": self.round_number,
            "era": self.era,
            "countries": {
                c.id: {
                    "private_value": round(c.private_value, 2),
                    "is_active": c.is_active,
                    "perceived_values": {
                        k: round(v, 2) for k, v in c.perceived_values.items()
                    }
                }
                for c in self.countries.values()
            }
        }
    
    def print_status(self):
        """Print current status of the simulation."""
        status = self.get_status()
        print(f"\n{'='*60}")
        print(f"Round {status['round']} | Era {status['era']}")
        print(f"{'='*60}")
        print(f"{'Country':<10} {'Private Value':<15} {'Status':<10}")
        print(f"{'-'*60}")
        
        for country_id, info in sorted(status['countries'].items()):
            status_str = "Active" if info['is_active'] else "Removed"
            print(f"{country_id:<10} {info['private_value']:<15.2f} {status_str:<10}")
    
    def print_results(self, results: List[Dict]):
        """Print results from a round."""
        print(f"\n{'='*60}")
        print(f"Round {self.round_number} Results")
        print(f"{'='*60}")
        
        for result in results:
            country1_id = result['country1']
            country2_id = result['country2']
            action1 = result['action1']
            action2 = result['action2']
            outcome = result['outcome']
            
            print(f"\nCountry {country1_id} ({action1}) vs Country {country2_id} ({action2})")
            
            if outcome == "bargain":
                print(f"  → Both countries bargained successfully")
                print(f"  → Country {country1_id} value: {result['country1_new_value']:.2f} (+{result['country1_gain']:.2f})")
                print(f"  → Country {country2_id} value: {result['country2_new_value']:.2f} (+{result['country2_gain']:.2f})")
            elif outcome == "attack_success":
                print(f"  → Country {result['attacker']} successfully attacked Country {result['defender']}")
                print(f"  → Attacker value: {result['attacker_new_value']:.2f}")
                print(f"  → Defender removed from game")
            elif outcome == "defense_success":
                print(f"  → Country {result['attacker']} attacked but defense was successful")
                print(f"  → Country {result['attacker']} value: {result['attacker_new_value']:.2f}")
                print(f"  → Country {result['defender']} value: {result['defender_new_value']:.2f}")


def main():
    """Main function to run the simulation."""
    print("Deterrence Modeling Simulation")
    print("=" * 60)
    
    # Create simulation
    sim = DeterrenceSimulation(num_countries=10, seed=None)
    
    # Print initial status
    print("\nInitial State:")
    sim.print_status()
    
    # Run multiple rounds
    num_rounds = 5
    for _ in range(num_rounds):
        results = sim.run_round()
        sim.print_results(results)
        sim.print_status()
        
        # Check if we have enough active countries to continue
        active_countries = [c for c in sim.countries.values() if c.is_active]
        if len(active_countries) < 2:
            print("\nNot enough active countries to continue simulation.")
            break
    
    print("\n" + "=" * 60)
    print("Simulation Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()

