"""
Deterrence Modeling Simulation

This simulation demonstrates the concept of deterrence through a bargaining model
where countries can choose to attack or bargain with each other.
"""

import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# ============================================================================
# SIMULATION PARAMETERS - Easily adjustable
# ============================================================================

# Initial Setup
NUM_COUNTRIES = 20
INITIAL_VALUE_MIN = 10
INITIAL_VALUE_MAX = 10000

# Perceived Values
PERCEIVED_VALUE_ACCURACY = 0.15  # Perceived values are within 15% of true value (0.85-1.15)

# Growth
GROWTH_RATE_MIN = 0.01  # 1% minimum growth per round
GROWTH_RATE_MAX = 0.08  # 8% maximum growth per round

# Attack Mechanics
ATTACK_COST_PERCENTAGE = 0.15  # Base cost (before discounts) as % of total value after acquisition
FAILED_ATTACK_COST_PERCENTAGE = 0.50  # Cost is 50% of attacker's value if attack fails
ATTACK_SUCCESS_DISCOUNT_CAP = 0.50  # Successful attack costs can be discounted up to 50% when attacker >> defender
ATTACKER_DEFENSE_LOSS_PERCENTAGE = 0.10  # Attacker loses 10% of value when defense succeeds
DEFENDER_DEFENSE_LOSS_PERCENTAGE = 0.05  # Defender loses 5% of value when defense succeeds
MAX_GAIN_MULTIPLIER = 2.0  # Smaller countries can't gain more than doubling their value (no total takeover)
PERCEIVED_COST_ACCURACY = 0.15  # Perceived costs are within 15% of true costs (0.85-1.15)

# Bargain Mechanics
BARGAIN_SURPLUS_PERCENTAGE = .30  # Total surplus of 30% randomly split between countries (0-30%)
BARGAIN_EV_PERCENTAGE = 0.10  # Expected value of bargain is 10% (average of 0-20%)

# ============================================================================

def calculate_success_cost_multiplier(attacker_value: float, defender_value: float) -> float:
    """
    Successful attack costs are discounted when the attacker is significantly larger
    than the defender. Discount is capped at ATTACK_SUCCESS_DISCOUNT_CAP.
    """
    defender_value = max(defender_value, 1e-6)
    if attacker_value <= defender_value:
        return 1.0
    ratio = attacker_value / defender_value
    discount = min(ATTACK_SUCCESS_DISCOUNT_CAP, (ratio - 1.0) / ratio)
    return max(0.0, 1.0 - discount)


# ============================================================================


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
        Perceived odds are within 15% of the true odds (based on actual private values).
        """
        other_country = all_countries.get(other_id)
        if not other_country:
            return 0.5
        
        # Calculate true odds based on actual private values
        total = self.private_value + other_country.private_value
        if total == 0:
            return 0.5
        
        true_odds = self.private_value / total
        
        # Perceived odds are within PERCEIVED_VALUE_ACCURACY of true odds
        # Generate a random value within PERCEIVED_VALUE_ACCURACY of true_odds
        min_perceived = max(0.0, true_odds * (1.0 - PERCEIVED_VALUE_ACCURACY))
        max_perceived = min(1.0, true_odds * (1.0 + PERCEIVED_VALUE_ACCURACY))
        
        # Ensure we don't go below 0 or above 1
        if max_perceived < min_perceived:
            max_perceived = min_perceived
        
        perceived_odds = random.uniform(min_perceived, max_perceived)
        
        return perceived_odds
    
    def get_true_odds(self, other_id: int, all_countries: Dict[int, 'Country']) -> float:
        """
        Calculate true odds of winning based on actual private values.
        Formula: (private_value + other_private_value) / (total of both private values)
        """
        other_country = all_countries.get(other_id)
        if not other_country:
            return 0.5
        
        total = self.private_value + other_country.private_value
        if total == 0:
            return 0.5
        
        return self.private_value / total
    
    def get_perceived_attack_cost(self, other_id: int, all_countries: Dict[int, 'Country']) -> float:
        """
        Calculate the perceived cost of a successful attack.
        Perceived cost is within 15% of the true cost.
        """
        # Calculate true cost based on perceived values (what we think we'll gain)
        perceived_value_of_other = self.perceived_values.get(other_id, 0)
        total_after_acquisition = self.private_value + perceived_value_of_other
        multiplier = calculate_success_cost_multiplier(self.private_value, max(perceived_value_of_other, 0.0))
        true_cost = total_after_acquisition * ATTACK_COST_PERCENTAGE * multiplier
        
        # Perceived cost is within PERCEIVED_COST_ACCURACY of true cost
        min_perceived = true_cost * (1.0 - PERCEIVED_COST_ACCURACY)
        max_perceived = true_cost * (1.0 + PERCEIVED_COST_ACCURACY)
        perceived_cost = random.uniform(min_perceived, max_perceived)
        
        return max(0.0, perceived_cost)
    
    def get_perceived_failed_attack_cost(self) -> float:
        """
        Calculate the perceived cost of a failed attack.
        Perceived cost is within 15% of the true cost (50% of attacker's value).
        """
        true_cost = self.private_value * FAILED_ATTACK_COST_PERCENTAGE
        
        # Perceived cost is within PERCEIVED_COST_ACCURACY of true cost
        min_perceived = true_cost * (1.0 - PERCEIVED_COST_ACCURACY)
        max_perceived = true_cost * (1.0 + PERCEIVED_COST_ACCURACY)
        perceived_cost = random.uniform(min_perceived, max_perceived)
        
        return max(0.0, perceived_cost)
    
    def get_attack_cost(self, other_id: int, all_countries: Dict[int, 'Country']) -> float:
        """
        Calculate the perceived cost of attack (for decision-making).
        This uses perceived values and perceived cost accuracy.
        """
        return self.get_perceived_attack_cost(other_id, all_countries)
    
    def decide_action(self, other_id: int, all_countries: Dict[int, 'Country']) -> str:
        """
        Decide whether to attack or bargain.
        Countries attack if their perceived EV of attack is greater than their perceived EV of bargain.
        """
        other_country = all_countries.get(other_id)
        if not other_country or not other_country.is_active:
            return "bargain"
        
        odds = self.get_perceived_odds(other_id, all_countries)
        
        # Get perceived value of defender (what we think we'll gain)
        perceived_defender_value = self.perceived_values.get(other_id, 0)
        
        # Expected value of attack using PERCEIVED costs:
        # If win: gain defender's full value (perceived), then pay perceived cost (discounted by relative strength)
        total_after_acquisition = self.private_value + perceived_defender_value
        perceived_cost_of_total = self.get_perceived_attack_cost(other_id, all_countries)
        final_value_if_win = total_after_acquisition - perceived_cost_of_total
        expected_gain_if_win = final_value_if_win - self.private_value  # Net gain
        
        # If defense succeeds: attacker loses ATTACKER_DEFENSE_LOSS_PERCENTAGE and incurs failed attack cost
        perceived_failure_cost = self.get_perceived_failed_attack_cost()
        final_value_if_lose = max(self.private_value * (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE) - perceived_failure_cost, 0.0)
        expected_loss_if_lose = self.private_value - final_value_if_lose
        ev_attack = (odds * expected_gain_if_win) - ((1 - odds) * expected_loss_if_lose)
        
        # Expected value of bargain
        ev_bargain = self.private_value * BARGAIN_EV_PERCENTAGE
        
        # Attack if perceived EV of attack is greater than perceived EV of bargain
        if ev_attack > ev_bargain:
            return "attack"
        else:
            return "bargain"


class DeterrenceSimulation:
    """Main simulation class for the deterrence model."""
    
    def __init__(self, num_countries: int = NUM_COUNTRIES, seed: Optional[int] = None):
        """Initialize the simulation with specified number of countries."""
        if seed is not None:
            random.seed(seed)
        
        self.num_countries = num_countries
        self.countries: Dict[int, Country] = {}
        self.round_number = 0
        self.previous_total_value = 0.0
        self.previous_country_values: Dict[int, float] = {}
        self.country_stats: Dict[int, Dict[str, int]] = {}  # Track attacks won, lost, defended
        self.country_growth_rates: Dict[int, float] = {}  # Track growth rate for each country
        
        self._initialize_countries()
    
    def _initialize_countries(self):
        """Initialize all countries with random private values and perceived values."""
        # Generate private values
        private_values = {}
        for i in range(1, self.num_countries + 1):
            private_values[i] = random.uniform(INITIAL_VALUE_MIN, INITIAL_VALUE_MAX)
        
        # Create countries and set perceived values
        for i in range(1, self.num_countries + 1):
            perceived_values = {}
            for j in range(1, self.num_countries + 1):
                if i != j:
                    # Perceived value is within PERCEIVED_VALUE_ACCURACY of the other country's private value
                    base_value = private_values[j]
                    perceived_values[j] = random.uniform(
                        base_value * (1.0 - PERCEIVED_VALUE_ACCURACY),
                        base_value * (1.0 + PERCEIVED_VALUE_ACCURACY)
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
                        true_value * (1.0 - PERCEIVED_VALUE_ACCURACY),
                        true_value * (1.0 + PERCEIVED_VALUE_ACCURACY)
                    )
                
                # Update perception of country2
                if country2_id in other_country.perceived_values:
                    true_value = country2.private_value
                    other_country.perceived_values[country2_id] = random.uniform(
                        true_value * (1.0 - PERCEIVED_VALUE_ACCURACY),
                        true_value * (1.0 + PERCEIVED_VALUE_ACCURACY)
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
        
        # Store initial values for cost calculations
        attacker_initial_value = attacker.private_value
        defender_initial_value = defender.private_value
        
        # Determine actual outcome based on odds
        attack_succeeds = random.random() < attacker_odds
        
        if attack_succeeds:
            # Attacker wins: defender's value goes to 0, attacker gains that value, then cost is imposed
            # Cost is ATTACK_COST_PERCENTAGE of the TOTAL value after acquisition, discounted by relative strength
            # BUT: smaller countries are capped at MAX_GAIN_MULTIPLIER times their value (no total takeover)
            max_gain = attacker_initial_value * (MAX_GAIN_MULTIPLIER - 1.0)
            actual_gain = min(defender_initial_value, max_gain)
            defender.private_value = 0
            attacker.private_value = attacker_initial_value + actual_gain
            total_value = attacker.private_value  # Total after acquisition
            multiplier = calculate_success_cost_multiplier(attacker_initial_value, defender_initial_value)
            cost = total_value * ATTACK_COST_PERCENTAGE * multiplier
            attacker.private_value = max(attacker.private_value - cost, 0.0)
            
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
            # Defense successful: attacker loses more value than defender
            attacker.private_value *= (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE)
            defender.private_value *= (1.0 - DEFENDER_DEFENSE_LOSS_PERCENTAGE)
            
            # Failed attacks incur a cost based on the attacker's initial value
            failure_cost = attacker_initial_value * FAILED_ATTACK_COST_PERCENTAGE
            attacker.private_value = max(attacker.private_value - failure_cost, 0.0)
            
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
        Total surplus is 20%, randomly split between the two countries.
        One country gets 0-20%, the other gets the remainder (20% - first country's %).
        """
        country1 = self.countries[country1_id]
        country2 = self.countries[country2_id]
        
        # Randomly split the BARGAIN_SURPLUS_PERCENTAGE total surplus
        # First country gets a random percentage between 0% and BARGAIN_SURPLUS_PERCENTAGE
        country1_percentage = random.uniform(0.0, BARGAIN_SURPLUS_PERCENTAGE)
        # Second country gets the remainder
        country2_percentage = BARGAIN_SURPLUS_PERCENTAGE - country1_percentage
        
        # Calculate gains based on each country's private value
        gain1 = country1.private_value * country1_percentage
        gain2 = country2.private_value * country2_percentage
        
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
        
        # Store previous country values before the round
        self.previous_country_values = {
            c.id: c.private_value for c in self.countries.values() if c.is_active
        }
        
        # Apply random growth to each active country (1% to 8% per round)
        # Reset growth rates for the round
        self.country_growth_rates = {}
        for country in self.countries.values():
            if country.is_active:
                growth_rate = random.uniform(GROWTH_RATE_MIN, GROWTH_RATE_MAX)
                self.country_growth_rates[country.id] = growth_rate
                country.private_value *= (1 + growth_rate)
        
        # Count countries at start of round (after growth, before interactions)
        self.countries_at_start = sum(1 for c in self.countries.values() if c.is_active)
        
        # Initialize country stats for this round
        for country_id in self.countries.keys():
            if country_id not in self.country_stats:
                self.country_stats[country_id] = {'attacks_won': 0, 'attacks_lost': 0, 'defended': 0, 'attacks_attempted': 0}
            else:
                # Reset for new round
                self.country_stats[country_id] = {'attacks_won': 0, 'attacks_lost': 0, 'defended': 0, 'attacks_attempted': 0}
        
        # Calculate and display total value at the beginning of the round
        round_start_total = self.get_total_value()
        change = round_start_total - self.previous_total_value
        
        print(f"\n{'='*60}")
        print(f"Round {self.round_number}")
        print(f"{'='*60}")
        print(f"Total Value: {round_start_total:.2f}")
        if self.previous_total_value > 0:
            change_str = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
            print(f"Change from previous round: {change_str}")
        else:
            print(f"Change from previous round: N/A (initial round)")
        print(f"{'='*60}")
        
        results = []
        
        # All rounds use round-robin format (each country interacts with all others)
        pairs = self._get_round_robin_pairs()
        
        # Process each pair
        for country1_id, country2_id in pairs:
            country1 = self.countries[country1_id]
            country2 = self.countries[country2_id]
            
            if not country1.is_active or not country2.is_active:
                continue
            
            # Store initial values before interaction
            country1_initial = country1.private_value
            country2_initial = country2.private_value
            
            # Get perceived values
            country1_perceived_of_2 = country1.perceived_values.get(country2_id, 0)
            country2_perceived_of_1 = country2.perceived_values.get(country1_id, 0)
            
            # Calculate expected values for both countries
            # For country1 - Perceived values (using perceived costs with strength discounts)
            perceived_odds1 = country1.get_perceived_odds(country2_id, self.countries)
            total_after_acquisition1 = country1.private_value + country1_perceived_of_2
            perceived_cost1 = country1.get_perceived_attack_cost(country2_id, self.countries)
            final_value_if_win1 = total_after_acquisition1 - perceived_cost1
            perceived_gain_if_win1 = final_value_if_win1 - country1.private_value  # Net gain
            perceived_failure_cost1 = country1.get_perceived_failed_attack_cost()
            failure_value_if_lose1 = max(country1.private_value * (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE) - perceived_failure_cost1, 0.0)
            perceived_loss_if_lose1 = country1.private_value - failure_value_if_lose1
            ev_attack1_perceived = (perceived_odds1 * perceived_gain_if_win1) - ((1 - perceived_odds1) * perceived_loss_if_lose1)
            # Expected value of bargain for country1
            ev_bargain1 = country1.private_value * BARGAIN_EV_PERCENTAGE
            
            # For country1 - Actual values using TRUE odds (based on relative strength)
            # Actual EV should reflect the true probability of winning, not perceived
            true_odds1 = country1_initial / (country1_initial + country2_initial) if (country1_initial + country2_initial) > 0 else 0.5
            
            # Actual EV calculation from country1's perspective using TRUE odds:
            # Smaller countries are capped at MAX_GAIN_MULTIPLIER times their value (no total takeover)
            max_gain1 = country1_initial * (MAX_GAIN_MULTIPLIER - 1.0)  # Can't gain more than MAX_GAIN_MULTIPLIER
            actual_gain_if_win1 = min(country2_initial, max_gain1)  # Capped gain
            total_after_acquisition1 = country1_initial + actual_gain_if_win1  # Total after acquiring defender
            multiplier1 = calculate_success_cost_multiplier(country1_initial, country2_initial)
            actual_cost1 = total_after_acquisition1 * ATTACK_COST_PERCENTAGE * multiplier1
            value_if_win1 = total_after_acquisition1 - actual_cost1  # Final value if win (with cap)
            value_if_lose1 = max(country1_initial * (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE) - (country1_initial * FAILED_ATTACK_COST_PERCENTAGE), 0.0)  # Final value if lose
            expected_final_value1 = (true_odds1 * value_if_win1) + ((1 - true_odds1) * value_if_lose1)
            ev_attack1_actual = expected_final_value1 - country1_initial  # Change from initial value
            
            # For country2 - Perceived values (using perceived costs with strength discounts)
            perceived_odds2 = country2.get_perceived_odds(country1_id, self.countries)
            total_after_acquisition2 = country2.private_value + country2_perceived_of_1
            perceived_cost2 = country2.get_perceived_attack_cost(country1_id, self.countries)
            final_value_if_win2 = total_after_acquisition2 - perceived_cost2
            perceived_gain_if_win2 = final_value_if_win2 - country2.private_value  # Net gain
            perceived_failure_cost2 = country2.get_perceived_failed_attack_cost()
            failure_value_if_lose2 = max(country2.private_value * (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE) - perceived_failure_cost2, 0.0)
            perceived_loss_if_lose2 = country2.private_value - failure_value_if_lose2
            ev_attack2_perceived = (perceived_odds2 * perceived_gain_if_win2) - ((1 - perceived_odds2) * perceived_loss_if_lose2)
            # Expected value of bargain for country2
            ev_bargain2 = country2.private_value * BARGAIN_EV_PERCENTAGE
            
            # For country2 - Actual values using TRUE odds (based on relative strength)
            # Actual EV should reflect the true probability of winning, not perceived
            true_odds2 = country2_initial / (country1_initial + country2_initial) if (country1_initial + country2_initial) > 0 else 0.5
            
            # Actual EV calculation from country2's perspective using TRUE odds:
            # Smaller countries are capped at MAX_GAIN_MULTIPLIER times their value (no total takeover)
            max_gain2 = country2_initial * (MAX_GAIN_MULTIPLIER - 1.0)  # Can't gain more than MAX_GAIN_MULTIPLIER
            actual_gain_if_win2 = min(country1_initial, max_gain2)  # Capped gain
            total_after_acquisition2 = country2_initial + actual_gain_if_win2  # Total after acquiring defender
            multiplier2 = calculate_success_cost_multiplier(country2_initial, country1_initial)
            actual_cost2 = total_after_acquisition2 * ATTACK_COST_PERCENTAGE * multiplier2
            value_if_win2 = total_after_acquisition2 - actual_cost2  # Final value if win (with cap)
            value_if_lose2 = max(country2_initial * (1.0 - ATTACKER_DEFENSE_LOSS_PERCENTAGE) - (country2_initial * FAILED_ATTACK_COST_PERCENTAGE), 0.0)  # Final value if lose
            expected_final_value2 = (true_odds2 * value_if_win2) + ((1 - true_odds2) * value_if_lose2)
            ev_attack2_actual = expected_final_value2 - country2_initial  # Change from initial value
            
            # Each country decides their action
            action1 = country1.decide_action(country2_id, self.countries)
            action2 = country2.decide_action(country1_id, self.countries)
            
            # Track attacks attempted
            if action1 == "attack":
                if country1_id in self.country_stats:
                    self.country_stats[country1_id]['attacks_attempted'] += 1
            if action2 == "attack":
                if country2_id in self.country_stats:
                    self.country_stats[country2_id]['attacks_attempted'] += 1
            
            # Resolve the interaction
            if action1 == "attack" and action2 == "attack":
                # Both attack - resolve as mutual attack (attacker1 attacks first)
                outcome, details = self._resolve_attack(country1_id, country2_id)
                result = {
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "country1_initial": country1_initial,
                    "country2_initial": country2_initial,
                    "country1_perceived_of_2": country1_perceived_of_2,
                    "country2_perceived_of_1": country2_perceived_of_1,
                    "country1_ev_attack_perceived": ev_attack1_perceived,
                    "country1_ev_attack_actual": ev_attack1_actual,
                    "country1_ev_bargain": ev_bargain1,
                    "country2_ev_attack_perceived": ev_attack2_perceived,
                    "country2_ev_attack_actual": ev_attack2_actual,
                    "country2_ev_bargain": ev_bargain2,
                    "country1_perceived_odds": perceived_odds1,
                    "country1_true_odds": true_odds1,
                    "country2_perceived_odds": perceived_odds2,
                    "country2_true_odds": true_odds2,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    "true_odds": true_odds1,
                    "attack_succeeded": outcome == "attack_success",
                    **details
                }
                self._update_country_stats(result)
                results.append(result)
            elif action1 == "attack":
                # Country1 attacks, country2 defends
                outcome, details = self._resolve_attack(country1_id, country2_id)
                result = {
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "country1_initial": country1_initial,
                    "country2_initial": country2_initial,
                    "country1_perceived_of_2": country1_perceived_of_2,
                    "country2_perceived_of_1": country2_perceived_of_1,
                    "country1_ev_attack_perceived": ev_attack1_perceived,
                    "country1_ev_attack_actual": ev_attack1_actual,
                    "country1_ev_bargain": ev_bargain1,
                    "country2_ev_attack_perceived": ev_attack2_perceived,
                    "country2_ev_attack_actual": ev_attack2_actual,
                    "country2_ev_bargain": ev_bargain2,
                    "country1_perceived_odds": perceived_odds1,
                    "country1_true_odds": true_odds1,
                    "country2_perceived_odds": perceived_odds2,
                    "country2_true_odds": true_odds2,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    "true_odds": true_odds1,
                    "attack_succeeded": outcome == "attack_success",
                    **details
                }
                self._update_country_stats(result)
                results.append(result)
            elif action2 == "attack":
                # Country2 attacks, country1 defends
                outcome, details = self._resolve_attack(country2_id, country1_id)
                result = {
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "country1_initial": country1_initial,
                    "country2_initial": country2_initial,
                    "country1_perceived_of_2": country1_perceived_of_2,
                    "country2_perceived_of_1": country2_perceived_of_1,
                    "country1_ev_attack_perceived": ev_attack1_perceived,
                    "country1_ev_attack_actual": ev_attack1_actual,
                    "country1_ev_bargain": ev_bargain1,
                    "country2_ev_attack_perceived": ev_attack2_perceived,
                    "country2_ev_attack_actual": ev_attack2_actual,
                    "country2_ev_bargain": ev_bargain2,
                    "country1_perceived_odds": perceived_odds1,
                    "country1_true_odds": true_odds1,
                    "country2_perceived_odds": perceived_odds2,
                    "country2_true_odds": true_odds2,
                    "action1": action1,
                    "action2": action2,
                    "outcome": outcome,
                    "true_odds": true_odds2,
                    "attack_succeeded": outcome == "attack_success",
                    **details
                }
                self._update_country_stats(result)
                results.append(result)
            else:
                # Both bargain
                details = self._resolve_bargain(country1_id, country2_id)
                results.append({
                    "round": self.round_number,
                    "country1": country1_id,
                    "country2": country2_id,
                    "country1_initial": country1_initial,
                    "country2_initial": country2_initial,
                    "country1_perceived_of_2": country1_perceived_of_2,
                    "country2_perceived_of_1": country2_perceived_of_1,
                    "country1_ev_attack_perceived": ev_attack1_perceived,
                    "country1_ev_attack_actual": ev_attack1_actual,
                    "country1_ev_bargain": ev_bargain1,
                    "country2_ev_attack_perceived": ev_attack2_perceived,
                    "country2_ev_attack_actual": ev_attack2_actual,
                    "country2_ev_bargain": ev_bargain2,
                    "country1_perceived_odds": perceived_odds1,
                    "country1_true_odds": true_odds1,
                    "country2_perceived_odds": perceived_odds2,
                    "country2_true_odds": true_odds2,
                    "action1": action1,
                    "action2": action2,
                    "outcome": "bargain",
                    **details
                })
        
        # Update previous_total_value for next round
        self.previous_total_value = self.get_total_value()
        
        # Store round_start_total for statistics calculation
        self.round_start_total = round_start_total
        
        return results
    
    def _update_country_stats(self, result: Dict):
        """Update country statistics based on attack outcomes."""
        outcome = result.get('outcome')
        attacker_id = result.get('attacker')
        defender_id = result.get('defender')
        
        if outcome == "attack_success":
            # Attacker won
            if attacker_id in self.country_stats:
                self.country_stats[attacker_id]['attacks_won'] += 1
            # Defender lost (and was removed)
            if defender_id in self.country_stats:
                self.country_stats[defender_id]['attacks_lost'] += 1
        elif outcome == "defense_success":
            # Attacker lost
            if attacker_id in self.country_stats:
                self.country_stats[attacker_id]['attacks_lost'] += 1
            # Defender successfully defended
            if defender_id in self.country_stats:
                self.country_stats[defender_id]['defended'] += 1
    
    def get_total_value(self) -> float:
        """Calculate the total value of all active countries."""
        return sum(c.private_value for c in self.countries.values() if c.is_active)
    
    def get_status(self) -> Dict:
        """Get current status of all countries."""
        return {
            "round": self.round_number,
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
        print(f"Round {status['round']}")
        print(f"{'='*60}")
        print(f"{'Country':<10} {'Private Value':<15} {'Status':<10} {'Growth Rate':<12} {'Attacks Attempted':<18} {'Attacks Won':<12} {'Attacks Lost':<13} {'Defended':<10} {'Change':<10} {'Change %':<10}")
        print(f"{'-'*130}")
        
        for country_id, info in sorted(status['countries'].items()):
            status_str = "Active" if info['is_active'] else "Removed"
            
            # Get growth rate for this country
            growth_rate = self.country_growth_rates.get(country_id, 0.0)
            growth_str = f"{growth_rate*100:.2f}%" if country_id in self.country_growth_rates else "N/A"
            
            # Get statistics
            stats = self.country_stats.get(country_id, {'attacks_won': 0, 'attacks_lost': 0, 'defended': 0, 'attacks_attempted': 0})
            attacks_attempted = stats['attacks_attempted']
            attacks_won = stats['attacks_won']
            attacks_lost = stats['attacks_lost']
            defended = stats['defended']
            
            # Calculate change from previous round
            previous_value = self.previous_country_values.get(country_id, info['private_value'])
            current_value = info['private_value']
            change = current_value - previous_value
            change_pct = (change / previous_value * 100) if previous_value > 0 else 0.0
            
            change_str = f"{change:+.2f}" if previous_value > 0 else "N/A"
            change_pct_str = f"{change_pct:+.2f}%" if previous_value > 0 else "N/A"
            
            print(f"{country_id:<10} {info['private_value']:<15.2f} {status_str:<10} {growth_str:<12} {attacks_attempted:<18} {attacks_won:<12} {attacks_lost:<13} {defended:<10} {change_str:<10} {change_pct_str:<10}")
    
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
            
            # Get initial values and perceived values
            c1_initial = result.get('country1_initial', 0)
            c2_initial = result.get('country2_initial', 0)
            c1_perceived = result.get('country1_perceived_of_2', 0)
            c2_perceived = result.get('country2_perceived_of_1', 0)
            c1_ev_attack_perceived = result.get('country1_ev_attack_perceived', 0)
            c1_ev_attack_actual = result.get('country1_ev_attack_actual', 0)
            c1_ev_bargain = result.get('country1_ev_bargain', 0)
            c2_ev_attack_perceived = result.get('country2_ev_attack_perceived', 0)
            c2_ev_attack_actual = result.get('country2_ev_attack_actual', 0)
            c2_ev_bargain = result.get('country2_ev_bargain', 0)
            c1_perceived_odds = result.get('country1_perceived_odds', 0)
            c1_true_odds = result.get('country1_true_odds', 0)
            c2_perceived_odds = result.get('country2_perceived_odds', 0)
            c2_true_odds = result.get('country2_true_odds', 0)
            
            print(f"\nCountry {country1_id} vs Country {country2_id}")
            print(f"  Initial Values: C{country1_id}={c1_initial:.2f}, C{country2_id}={c2_initial:.2f}")
            print(f"  Perceived Values: C{country1_id} perceives C{country2_id}={c1_perceived:.2f}, C{country2_id} perceives C{country1_id}={c2_perceived:.2f}")
            print(f"  Expected Values (Attack):")
            print(f"    C{country1_id}: Perceived EV={c1_ev_attack_perceived:.2f}, Actual EV={c1_ev_attack_actual:.2f}, Bargain EV={c1_ev_bargain:.2f} → Chooses: {action1}")
            print(f"    C{country2_id}: Perceived EV={c2_ev_attack_perceived:.2f}, Actual EV={c2_ev_attack_actual:.2f}, Bargain EV={c2_ev_bargain:.2f} → Chooses: {action2}")
            print(f"  Win Probabilities:")
            print(f"    C{country1_id}: Perceived={c1_perceived_odds*100:.2f}%, Actual={c1_true_odds*100:.2f}%")
            print(f"    C{country2_id}: Perceived={c2_perceived_odds*100:.2f}%, Actual={c2_true_odds*100:.2f}%")
            
            if outcome == "bargain":
                print(f"  → Both countries bargained successfully")
                print(f"  → Country {country1_id} value: {result['country1_new_value']:.2f} (+{result['country1_gain']:.2f})")
                print(f"  → Country {country2_id} value: {result['country2_new_value']:.2f} (+{result['country2_gain']:.2f})")
            elif outcome == "attack_success":
                attacker_id = result['attacker']
                defender_id = result['defender']
                true_odds = result.get('true_odds', 0)
                print(f"  → Country {attacker_id} attacked Country {defender_id}")
                print(f"  → Actual odds of success: {true_odds*100:.2f}%")
                print(f"  → Attack was SUCCESSFUL")
                print(f"  → Attacker value: {result['attacker_new_value']:.2f}")
                print(f"  → Defender removed from game")
            elif outcome == "defense_success":
                attacker_id = result['attacker']
                defender_id = result['defender']
                true_odds = result.get('true_odds', 0)
                print(f"  → Country {attacker_id} attacked Country {defender_id}")
                print(f"  → Actual odds of success: {true_odds*100:.2f}%")
                print(f"  → Attack FAILED (defense successful)")
                print(f"  → Country {attacker_id} value: {result['attacker_new_value']:.2f}")
                print(f"  → Country {defender_id} value: {result['defender_new_value']:.2f}")
    
    def print_round_statistics(self, results: List[Dict], is_last_round: bool = False):
        """Print statistics at the end of a round."""
        if not is_last_round:
            return
        
        # Calculate percentage change from start of round
        round_end_total = self.get_total_value()
        total_change = round_end_total - self.round_start_total
        percentage_change = (total_change / self.round_start_total * 100) if self.round_start_total > 0 else 0
        
        # Count bargains and attacks
        bargains = sum(1 for r in results if r['outcome'] == 'bargain')
        attacks = sum(1 for r in results if r['outcome'] in ['attack_success', 'defense_success'])
        total_interactions = len(results)
        
        # Count countries at end of round
        countries_at_end = sum(1 for c in self.countries.values() if c.is_active)
        
        print(f"\n{'='*60}")
        print(f"Round {self.round_number} Statistics")
        print(f"{'='*60}")
        print(f"Percentage change in total value: {percentage_change:+.2f}%")
        print(f"Number of bargains: {bargains}")
        print(f"Number of attacks: {attacks}")
        print(f"Total interactions: {total_interactions}")
        print(f"Countries at start of round: {self.countries_at_start}")
        print(f"Countries at end of round: {countries_at_end}")
        print(f"{'='*60}")


def main():
    """Main function to run the simulation."""
    print("Deterrence Modeling Simulation")
    print("=" * 60)
    
    # Create simulation
    sim = DeterrenceSimulation(num_countries=NUM_COUNTRIES, seed=None)
    
    # Print initial status
    print("\nInitial State:")
    initial_total = sim.get_total_value()
    print(f"Total Value: {initial_total:.2f}")
    sim.print_status()
    
    # Set previous values for the first round
    sim.previous_total_value = initial_total
    sim.previous_country_values = {
        c.id: c.private_value for c in sim.countries.values() if c.is_active
    }
    
    # Run one complete round-robin round
    results = sim.run_round()
    
    sim.print_results(results)
    sim.print_status()
    
    # Print end-of-round statistics (this is the last round)
    sim.print_round_statistics(results, is_last_round=True)
    
    print("\n" + "=" * 60)
    print("Simulation Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()

