# Deterrence Simulation Visualization Guide

## Overview

This guide explains the visualization options for understanding deterrence dynamics in the simulation. The visualizations help answer key questions about how attack costs, perceived vs actual costs, and strategic decisions affect deterrence—especially how bargaining keeps countries out of costly wars (nuclear escalation will be added later).

## Key Deterrence Concepts Visualized

### 1. **Deterrence Effectiveness**
   - **What it measures**: How well the threat of attack costs prevents countries from attacking
   - **Key metric**: Attack rate vs Bargain rate
   - **Interpretation**: Lower attack rates = stronger deterrence

### 2. **Perception vs Reality**
   - **What it measures**: How misperception of costs affects decision-making
   - **Key metric**: Perceived EV vs Actual EV
   - **Interpretation**: Countries with accurate perceptions make better decisions

### 3. **System Stability**
   - **What it measures**: How deterrence preserves countries and total value
   - **Key metrics**: Country survival, Total system value
   - **Interpretation**: Strong deterrence = more countries survive, more value preserved

### 4. **Value Preserved by Bargaining**
   - **What it measures**: How much loss is avoided when countries choose diplomacy
   - **Key metric**: Value saved by bargains (per round and cumulative)
   - **Interpretation**: Rising savings indicate that deterrence is doing real economic work

## Available Visualizations

### 1. Attack Rate vs Bargain Rate Over Time
**File**: `1_attack_vs_bargain_rate.png`

**What it shows**:
- Percentage of interactions that result in attacks vs bargains
- How deterrence effectiveness changes over rounds

**Key insights**:
- High bargain rate = strong deterrence
- Decreasing attack rate over time = learning/adaptation
- Stable ratios = equilibrium reached

**Deterrence indicator**: Higher green area (bargains) = better deterrence

---

### 1b. Value Saved by Bargains
**File**: `1b_bargain_value_saved.png`

**What it shows**:
- Estimated value preserved each round because countries chose to bargain instead of launch negative-EV attacks
- Cumulative value saved across the simulation

**How it's calculated**:
- For every bargain interaction we take the negative of each country's actual EV of attack (when it is negative) as the value “saved” by not launching the attack
- These savings are summed per round and cumulatively

**Key insights**:
- Tall bars indicate rounds where diplomacy prevented especially costly wars
- The cumulative line shows how deterrence compounds over time

**Deterrence indicator**: Rising cumulative line = bargaining consistently prevents destructive attacks

---

### 2. Perceived vs Actual EV Scatter Plot
**File**: `2_perceived_vs_actual_ev.png`

**What it shows**:
- Each point represents a country's decision point
- X-axis: Perceived EV of attack
- Y-axis: Actual EV of attack
- Color: Red = chose attack, Blue = chose bargain (deterred)

**Key insights**:
- Points above diagonal = underestimated costs (attacked when shouldn't)
- Points below diagonal = overestimated costs (deterred when could attack)
- Clustering near diagonal = accurate perception
- Red points in negative EV region = irrational attacks

**Deterrence indicator**: More blue points = more deterrence; points closer to diagonal = better information

---

### 3. Country Survival Over Time
**File**: `3_country_survival.png`

**What it shows**:
- Number of active countries remaining each round
- Impact of attacks on system stability

**Key insights**:
- Steeper decline = weaker deterrence
- Flat line = perfect deterrence (no eliminations)
- Stabilization = equilibrium reached

**Deterrence indicator**: Higher line = better deterrence (fewer eliminations)

---

### 4. Total System Value Over Time
**File**: `4_total_value_over_time.png`

**What it shows**:
- Total wealth in the system across rounds
- How attacks vs bargains affect overall value

**Key insights**:
- Declining value = attacks destroying wealth
- Increasing value = growth + bargaining creating value
- Steep drops = major attacks occurred

**Deterrence indicator**: Higher/rising value = better deterrence (bargaining preserves value)

---

### 5. Attack Success Rate Over Time
**File**: `5_attack_success_rate.png`

**What it shows**:
- Percentage of attacks that succeed
- Effectiveness of defense

**Key insights**:
- High success rate = weak defenses or strong attackers
- Low success rate = strong defenses
- Changes over time = adaptation or selection effects

**Deterrence indicator**: Lower success rate = stronger defense = better deterrence

---

### 6. Expected Value Comparison
**File**: `6_ev_comparison.png`

**What it shows**:
- Side-by-side comparison of:
  - Perceived EV of attack
  - Actual EV of attack  
  - EV of bargain
- For sampled interactions

**Key insights**:
- When bargain EV > attack EV = rational to be deterred
- When perceived EV > actual EV = overestimated benefits
- When actual EV < 0 = attack is irrational

**Deterrence indicator**: More cases where bargain EV > attack EV = better deterrence

---

## Advanced Visualization Ideas

### 7. **Attack Network Graph** (Not yet implemented)
- Network diagram showing attack relationships
- Nodes = countries (size = value, color = survival status)
- Edges = attacks (color = success/failure, thickness = frequency)
- Shows clustering, attack patterns, and strategic relationships

### 8. **Cost-Benefit Decision Matrix** (Not yet implemented)
- Heatmap showing attack decisions
- X-axis: Relative strength ratio
- Y-axis: Perceived cost percentage
- Color: Attack rate in that region
- Shows where deterrence works vs fails

### 9. **Parameter Sensitivity Analysis** (Not yet implemented)
- Multiple simulations with different cost parameters
- Heatmap showing attack rates across parameter space
- Identifies deterrence thresholds

### 10. **Value Distribution Over Time** (Not yet implemented)
- Violin plots showing distribution of country values
- Shows concentration vs dispersion
- Reveals inequality and power dynamics

---

## How to Use the Visualizations

### Running the Visualization Script

```bash
python visualize_deterrence.py
```

This will:
1. Run a 5-round simulation
2. Generate all 7 core visualizations
3. Save them to `visualizations/` directory

### Customizing

Edit `visualize_deterrence.py`:
- `NUM_ROUNDS`: Change number of rounds to simulate
- `SEED`: Set for reproducibility
- Modify individual plot functions for custom styling

### Interpreting Results

**Strong Deterrence Indicators**:
- High bargain rate (>70%)
- Low attack rate (<30%)
- High country survival (>90% after 5 rounds)
- Increasing or stable total value
- Low attack success rate (<50%)
- Most decisions show bargain EV > attack EV

**Weak Deterrence Indicators**:
- High attack rate (>50%)
- Rapid country elimination
- Declining total value
- High attack success rate
- Many attacks with negative actual EV

---

## Research Questions These Visualizations Answer

1. **Does the cost structure effectively deter attacks?**
   → Look at Attack vs Bargain Rate plot

2. **How does misperception affect deterrence?**
   → Look at Perceived vs Actual EV plot

3. **Is the system stable over time?**
   → Look at Country Survival and Total Value plots

4. **Are countries making rational decisions?**
   → Look at EV Comparison plot

5. **What's the optimal cost structure?**
   → Run parameter sensitivity analysis (advanced)

---

## Tips for Effective Analysis

1. **Run multiple simulations** with different seeds to see patterns
2. **Compare scenarios** by running with different cost parameters
3. **Focus on trends** rather than single-round snapshots
4. **Look for equilibria** where rates stabilize
5. **Identify outliers** that might indicate special cases

---

## Future Enhancements

- Interactive dashboards with Plotly/Dash
- Real-time animation of simulation
- Comparative analysis across parameter sets
- Machine learning to predict deterrence effectiveness
- Export data for statistical analysis

