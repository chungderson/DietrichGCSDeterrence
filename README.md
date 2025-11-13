# DietrichGCS Deterrence Modeling

A simulation demonstrating the concept of deterrence through a bargaining model where countries can choose to attack or bargain with each other.

## Overview

This simulation models international relations through a game-theoretic framework where:
- Each country has a private value (strength/resources)
- Countries have imperfect information about each other's values
- Countries can choose to attack or bargain with each other
- Outcomes depend on relative strengths and strategic decisions

## Model Details

### Initial Setup
- **10 countries** participate in the simulation
- Each country starts with a **random private value between 100 and 1000**
- Each country has **perceived values** for all other countries (within 15% of the true private value)

### Game Mechanics

#### Actions
Each country can choose one of two actions when interacting with another country:
- **Attack**: Attempt to conquer the other country
- **Bargain**: Negotiate peacefully for mutual benefit

#### Attack Mechanics
- **Perceived odds of winning**: `(private_value + perceived_value_of_other) / (total sum of perceived values)`
- **Cost of attack**: 10% of the total perceived values
- **If attack succeeds**:
  - Attacker gains all of defender's value
  - Attack cost is deducted
  - Defender is removed from the game
- **If defense succeeds**:
  - Both countries lose 10% of their value

#### Bargain Mechanics
- Both countries gain 5% of their private value
- No risk of loss

#### Information Updates
After each interaction, all other countries' perceived values of the interacting countries are re-rated within 15% of the true value.

### Round Structure

1. **First Era**: Countries are paired as (1,2), (3,4), (5,6), (7,8), (9,10)
2. **Subsequent Eras**: Round-robin format where each country interacts with every other active country

## Usage

Run the simulation:

```bash
python deterrence_simulation.py
```

The simulation will:
1. Initialize 10 countries with random values
2. Run multiple rounds of interactions
3. Display results after each round
4. Show the final state of all countries

## Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

## Future Enhancements

- GUI visualization
- Different decision-making strategies
- Configurable parameters
- Statistical analysis of outcomes
- Export results to CSV/JSON

