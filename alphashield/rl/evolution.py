"""Evolutionary search for meta-optimization.

Implements simple evolutionary strategy for optimizing global hyper-parameters.
"""
from typing import Dict, Any, List, Tuple, Optional, Callable
import numpy as np
from copy import deepcopy


class EvolutionaryOptimizer:
    """Simple evolutionary strategy for meta-parameter optimization.
    
    Uses (μ, λ) evolution strategy with Gaussian mutations.
    """
    
    def __init__(self, 
                 population_size: int = 20,
                 elite_frac: float = 0.3,
                 sigma: float = 0.1,
                 patience: int = 5,
                 epsilon_improve: float = 0.01,
                 seed: Optional[int] = None):
        """Initialize evolutionary optimizer.
        
        Parameters
        ----------
        population_size : int
            Number of candidates per generation
        elite_frac : float
            Fraction of population to keep as elites (default 0.3)
        sigma : float
            Mutation standard deviation (default 0.1)
        patience : int
            Generations without improvement before stopping
        epsilon_improve : float
            Minimum improvement to count as progress
        seed : int, optional
            Random seed
        """
        self.population_size = population_size
        self.n_elite = max(1, int(population_size * elite_frac))
        self.sigma = sigma
        self.patience = patience
        self.epsilon_improve = epsilon_improve
        self.rng = np.random.default_rng(seed)
        
        self.best_candidate = None
        self.best_fitness = -np.inf
        self.history = []
    
    def _mutate(self, candidate: Dict[str, float], bounds: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Mutate a candidate with Gaussian noise.
        
        Parameters
        ----------
        candidate : dict
            Parameter dictionary
        bounds : dict
            Parameter bounds {param_name: (min, max)}
        
        Returns
        -------
        dict
            Mutated candidate
        """
        mutated = {}
        for key, value in candidate.items():
            if key in bounds:
                low, high = bounds[key]
                noise = self.rng.normal(0, self.sigma * (high - low))
                new_value = np.clip(value + noise, low, high)
                mutated[key] = float(new_value)
            else:
                mutated[key] = value
        return mutated
    
    def _crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Dict[str, float]:
        """Simple uniform crossover between two parents.
        
        Parameters
        ----------
        parent1 : dict
            First parent
        parent2 : dict
            Second parent
        
        Returns
        -------
        dict
            Offspring
        """
        offspring = {}
        for key in parent1.keys():
            if self.rng.random() < 0.5:
                offspring[key] = parent1[key]
            else:
                offspring[key] = parent2[key]
        return offspring
    
    def initialize_population(self, base_config: Dict[str, float], 
                            bounds: Dict[str, Tuple[float, float]]) -> List[Dict[str, float]]:
        """Initialize population around base configuration.
        
        Parameters
        ----------
        base_config : dict
            Starting configuration
        bounds : dict
            Parameter bounds
        
        Returns
        -------
        list
            Initial population
        """
        population = [deepcopy(base_config)]
        
        # Generate variations
        for _ in range(self.population_size - 1):
            candidate = self._mutate(base_config, bounds)
            population.append(candidate)
        
        return population
    
    def evolve_generation(self, population: List[Dict[str, float]], 
                         fitness_scores: List[float],
                         bounds: Dict[str, Tuple[float, float]]) -> List[Dict[str, float]]:
        """Evolve population for one generation.
        
        Parameters
        ----------
        population : list
            Current population
        fitness_scores : list
            Fitness scores for current population
        bounds : dict
            Parameter bounds
        
        Returns
        -------
        list
            Next generation population
        """
        # Sort by fitness
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elites = [population[i] for i in sorted_indices[:self.n_elite]]
        
        # Track best
        best_idx = sorted_indices[0]
        if fitness_scores[best_idx] > self.best_fitness:
            self.best_fitness = fitness_scores[best_idx]
            self.best_candidate = deepcopy(population[best_idx])
        
        # Generate next generation
        next_gen = elites.copy()
        
        while len(next_gen) < self.population_size:
            # Select parents from elites
            parent1 = elites[self.rng.integers(0, len(elites))]
            parent2 = elites[self.rng.integers(0, len(elites))]
            
            # Crossover and mutate
            if self.rng.random() < 0.7:
                offspring = self._crossover(parent1, parent2)
            else:
                offspring = deepcopy(parent1)
            
            offspring = self._mutate(offspring, bounds)
            next_gen.append(offspring)
        
        return next_gen
    
    def optimize(self, 
                fitness_fn: Callable[[Dict[str, float]], float],
                base_config: Dict[str, float],
                bounds: Dict[str, Tuple[float, float]],
                max_generations: int = 50) -> Tuple[Dict[str, float], float]:
        """Run evolutionary optimization.
        
        Parameters
        ----------
        fitness_fn : callable
            Function that takes config dict and returns fitness score
        base_config : dict
            Starting configuration
        bounds : dict
            Parameter bounds {param: (min, max)}
        max_generations : int
            Maximum number of generations
        
        Returns
        -------
        tuple
            (best_config, best_fitness)
        """
        # Initialize
        population = self.initialize_population(base_config, bounds)
        generations_without_improvement = 0
        prev_best_fitness = -np.inf
        
        for gen in range(max_generations):
            # Evaluate fitness
            fitness_scores = [fitness_fn(candidate) for candidate in population]
            
            # Track history
            self.history.append({
                'generation': gen,
                'best_fitness': max(fitness_scores),
                'mean_fitness': np.mean(fitness_scores),
                'std_fitness': np.std(fitness_scores)
            })
            
            # Check for improvement
            current_best = max(fitness_scores)
            if current_best - prev_best_fitness < self.epsilon_improve:
                generations_without_improvement += 1
            else:
                generations_without_improvement = 0
            
            # Early stopping
            if generations_without_improvement >= self.patience:
                break
            
            prev_best_fitness = current_best
            
            # Evolve
            population = self.evolve_generation(population, fitness_scores, bounds)
        
        return self.best_candidate, self.best_fitness


def optimize_reward_weights(replay_buffer, 
                           base_config: Dict[str, float],
                           n_days: int = 30,
                           max_generations: int = 30) -> Dict[str, float]:
    """Optimize reward weights using evolutionary search.
    
    Parameters
    ----------
    replay_buffer : ReplayBuffer
        Experience replay buffer
    base_config : dict
        Current reward configuration
    n_days : int
        Number of days to evaluate over
    max_generations : int
        Maximum generations
    
    Returns
    -------
    dict
        Optimized reward configuration
    """
    from alphashield.rl.reward import compute_reward
    
    # Define bounds for reward weights
    bounds = {
        'alpha': (0.2, 0.6),     # wealth weight
        'beta': (0.05, 0.25),    # coverage weight
        'gamma': (0.05, 0.25),   # fairness weight
        'delta': (0.05, 0.20),   # satisfaction weight
        'lambda1': (0.05, 0.20), # drawdown penalty
        'lambda2': (0.0, 0.10),  # anomaly penalty
        'lambda3': (0.0, 0.10),  # tax risk penalty
    }
    
    # Sample experiences for evaluation
    experiences = replay_buffer.sample(n=1000, recent_days=n_days)
    
    if not experiences:
        return base_config
    
    def fitness_function(config: Dict[str, float]) -> float:
        """Evaluate fitness of a reward configuration.
        
        Fitness = average reward - volatility penalty - fairness violation penalty
        """
        rewards = []
        fairness_violations = 0
        
        for exp in experiences:
            metrics = exp.get('metrics', {})
            reward = compute_reward(metrics, config)
            rewards.append(reward)
            
            # Penalize fairness violations
            if metrics.get('fairness', 1.0) < 0.5:
                fairness_violations += 1
        
        if not rewards:
            return 0.0
        
        avg_reward = np.mean(rewards)
        volatility = np.std(rewards)
        fairness_penalty = fairness_violations / len(rewards)
        
        # Fitness balances reward, stability, and fairness
        fitness = avg_reward - 0.5 * volatility - 2.0 * fairness_penalty
        
        return float(fitness)
    
    # Run optimization
    optimizer = EvolutionaryOptimizer(
        population_size=20,
        elite_frac=0.3,
        sigma=0.1,
        patience=5,
        epsilon_improve=0.01
    )
    
    best_config, best_fitness = optimizer.optimize(
        fitness_fn=fitness_function,
        base_config=base_config,
        bounds=bounds,
        max_generations=max_generations
    )
    
    return best_config if best_config else base_config
