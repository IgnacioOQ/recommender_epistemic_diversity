"""Probabilistic model for *The effects of AI recommendation on epistemic diversity*.

Phase 1 (this codebase): standard two-armed bandit with independent
Beta-Bernoulli myopic Bayesian agents and a stubbed-out recommender
interface, faithful to §1-§2 of the paper.

See `papers/recommenders/README.md` for the layout.
"""

from .agent import BetaBernoulliAgent
from .bandit import BernoulliBandit
from .discovery import (
    discovered_by_last_k,
    discovered_by_posterior_gap,
    discovered_by_posterior_probability,
)
from .recommender import NullRecommender, Recommendation, Recommender
from .simulation import SimulationResult, run_simulation

__all__ = [
    "BernoulliBandit",
    "BetaBernoulliAgent",
    "NullRecommender",
    "Recommendation",
    "Recommender",
    "SimulationResult",
    "discovered_by_last_k",
    "discovered_by_posterior_gap",
    "discovered_by_posterior_probability",
    "run_simulation",
]
