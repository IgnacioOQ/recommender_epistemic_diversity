"""Recommender interface and Phase 1 stub.

The paper introduces the recommender in §3 as a function

    R_i^t = rho(h_i^t, pi_i^t, Z)  in  {A, B}

taking an agent's private history, their current posterior, and a
*common* latent state Z (shared across all agents per simulation) and
returning a recommendation for the next pull.

Phase 1 does **not** implement any real recommender; agents in §1-§2
choose without one. We still define the interface here so the agent
loop in `simulation.py` can be written once and reused in Phase 2.

To plug in a real recommender, subclass `Recommender` and implement
`recommend(...)`. The agent's conditioning step (Bayes update on R)
will live alongside that implementation in Phase 2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Recommendation:
    """A single recommendation handed to one agent at one step.

    `arm` is the recommended arm (`ARM_A` or `ARM_B`). `likelihood`, when
    provided, is P(R = arm | hidden truth, history, posterior, Z) — the
    quantity the agent needs for Bayesian conditioning in Phase 2. Phase 1
    recommenders may leave it `None`.
    """

    arm: int
    likelihood: Optional[float] = None


class Recommender(ABC):
    """Abstract recommender.

    A concrete recommender owns the common latent state Z (drawn once
    per simulation in `simulation.py`) and returns one `Recommendation`
    per agent per step.
    """

    @abstractmethod
    def recommend(
        self,
        agent_id: int,
        history: np.ndarray,
        posterior_alpha_beta: np.ndarray,
        rng: np.random.Generator,
    ) -> Optional[Recommendation]:
        """Return a recommendation for `agent_id`, or None to abstain.

        Parameters
        ----------
        agent_id : int
            Index of the agent receiving the recommendation.
        history : np.ndarray, shape (t, 2)
            The agent's private history. Row `s` is `[arm_pulled, outcome]`
            for step `s`. Empty (shape `(0, 2)`) at t = 0.
        posterior_alpha_beta : np.ndarray, shape (2, 2)
            The agent's current Beta posterior. Row `i` is `[alpha_i, beta_i]`
            for arm `i`.
        rng : np.random.Generator
            Per-agent (or per-step) RNG, for any randomness the recommender
            needs internally.
        """


class NullRecommender(Recommender):
    """No-op recommender. Always abstains.

    This is the Phase 1 default: the simulation runs the unaided regime
    of §1-§2 with the recommender hook present but inactive.
    """

    def recommend(
        self,
        agent_id: int,
        history: np.ndarray,
        posterior_alpha_beta: np.ndarray,
        rng: np.random.Generator,
    ) -> Optional[Recommendation]:
        return None
