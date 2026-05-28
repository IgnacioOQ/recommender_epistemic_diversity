"""Two-armed Bernoulli bandit.

Faithful to §1 of the paper: two arms A and B with mean payoffs
p_A > p_B. Payoffs are Bernoulli, which makes Beta-Bernoulli conjugacy
the natural prior choice for the agent (see `agent.py`).

Arm indexing convention used throughout the codebase:

    ARM_A = 0   # the better arm (p_A > p_B by construction)
    ARM_B = 1
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ARM_A: int = 0
ARM_B: int = 1
N_ARMS: int = 2


@dataclass(frozen=True)
class BernoulliBandit:
    """Two-armed Bernoulli bandit with arms A (better) and B (worse).

    Parameters
    ----------
    p_a, p_b : float
        Mean payoffs of arms A and B. Must lie in (0, 1) and satisfy p_a > p_b.
    """

    p_a: float
    p_b: float

    def __post_init__(self) -> None:
        for name, p in (("p_a", self.p_a), ("p_b", self.p_b)):
            if not 0.0 < p < 1.0:
                raise ValueError(f"{name} must lie in (0, 1); got {p}")
        if self.p_a <= self.p_b:
            raise ValueError(
                f"p_a must be strictly greater than p_b; got p_a={self.p_a}, p_b={self.p_b}"
            )

    @property
    def means(self) -> np.ndarray:
        """Mean payoffs indexed by arm: `means[ARM_A]`, `means[ARM_B]`."""
        return np.array([self.p_a, self.p_b])

    def pull(self, arm: int, rng: np.random.Generator) -> int:
        """Pull a single arm once and return the Bernoulli outcome (0 or 1)."""
        return int(rng.random() < self.means[arm])

    def pull_many(
        self, arms: np.ndarray, rng: np.random.Generator
    ) -> np.ndarray:
        """Vectorized pull. `arms[i] in {ARM_A, ARM_B}` → outcomes[i] in {0, 1}."""
        probs = self.means[arms]
        return (rng.random(size=arms.shape) < probs).astype(np.int8)
