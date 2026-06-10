"""Beta-Bernoulli myopic Bayesian agent.

Faithful to §1 of the paper:

- Each agent holds two **independent** Beta posteriors, one per arm.
- "Myopic Bayesian": at each step, pull the arm with higher posterior
  expected payoff. Ties broken uniformly at random.
- Posterior update is conjugate: after observing an outcome on the pulled
  arm, increment that arm's alpha (on success) or beta (on failure).
- Phase 1 stores the full history `(arm_pulled, outcome)` per step. This
  is what the recommender will need to read in Phase 2.

The agent does **not** know p_A or p_B. It only knows it is facing a
two-armed bandit and updates its independent priors from observation.

The recommender hook (`apply_recommendation`) is stubbed: in Phase 1 it
is never called because `NullRecommender.recommend` returns `None`.
Phase 2 will implement the Bayesian conditioning step on R_i^t here.
"""

from __future__ import annotations

import numpy as np

from .bandit import ARM_A, ARM_B, N_ARMS
from .recommender import Recommendation


class BetaBernoulliAgent:
    """One agent. Independent Beta(alpha_i, beta_i) prior per arm.

    Parameters
    ----------
    agent_id : int
        Identifier (used by recommenders that index per agent).
    prior_alpha_beta : np.ndarray, shape (2, 2), optional
        Row i is `[alpha_i, beta_i]` for arm i. Defaults to Beta(1, 1)
        (uniform) for both arms — i.e. no prior preference.
    """

    def __init__(
        self,
        agent_id: int,
        prior_alpha_beta: np.ndarray | None = None,
    ) -> None:
        self.agent_id = agent_id
        if prior_alpha_beta is None:
            prior_alpha_beta = np.array([[1.0, 1.0], [1.0, 1.0]])
        prior_alpha_beta = np.asarray(prior_alpha_beta, dtype=np.float64)
        if prior_alpha_beta.shape != (N_ARMS, 2):
            raise ValueError(
                f"prior_alpha_beta must have shape (2, 2); got {prior_alpha_beta.shape}"
            )
        if np.any(prior_alpha_beta <= 0):
            raise ValueError("Beta parameters must be strictly positive")

        self.alpha_beta: np.ndarray = prior_alpha_beta.copy()
        # Per-step record: rows are [arm_pulled, outcome]. Grown on each pull.
        self._history: list[tuple[int, int]] = []

    @property
    def history(self) -> np.ndarray:
        """History as an `(n_steps, 2)` int array of `[arm_pulled, outcome]` rows."""
        if not self._history:
            return np.empty((0, 2), dtype=np.int64)
        return np.asarray(self._history, dtype=np.int64)

    @property
    def posterior_means(self) -> np.ndarray:
        """Posterior mean of `p_i` for each arm: `alpha_i / (alpha_i + beta_i)`."""
        return self.alpha_beta[:, 0] / self.alpha_beta.sum(axis=1)

    def choose_arm(
        self,
        rng: np.random.Generator,
        recommendation: Recommendation | None = None,
    ) -> int:
        """Pick the arm with higher posterior expected payoff (ties random).

        A supplied `recommendation` is consumed according to which of its
        optional fields is set (see `Recommendation`):

        - `follow_prob` — behavioural nudge (interpretation 2): with that
          probability the recommended arm is pulled directly, bypassing the
          myopic comparison; otherwise the recommendation is ignored.
        - `outcome` — shared observation (interpretation 1): the draw is
          folded into the labeled arm's posterior via `observe_shared`,
          then the myopic comparison runs as usual.
        - neither — the explicit Bayes-conditioning route, delegated to
          `apply_recommendation` (not implemented).
        """
        if recommendation is not None:
            if recommendation.follow_prob is not None:
                if rng.random() < recommendation.follow_prob:
                    return int(recommendation.arm)
            elif recommendation.outcome is not None:
                self.observe_shared(recommendation.arm, recommendation.outcome)
            else:
                self.apply_recommendation(recommendation)

        means = self.posterior_means
        max_val = means.max()
        candidates = np.flatnonzero(means == max_val)
        if candidates.size == 1:
            return int(candidates[0])
        return int(rng.choice(candidates))

    def observe(self, arm: int, outcome: int) -> None:
        """Conjugate update on the pulled arm and append to history."""
        if arm not in (ARM_A, ARM_B):
            raise ValueError(f"arm must be ARM_A or ARM_B; got {arm}")
        if outcome not in (0, 1):
            raise ValueError(f"outcome must be 0 or 1; got {outcome}")
        if outcome == 1:
            self.alpha_beta[arm, 0] += 1.0
        else:
            self.alpha_beta[arm, 1] += 1.0
        self._history.append((int(arm), int(outcome)))

    def observe_shared(self, arm: int, outcome: int) -> None:
        """Conjugate update on a recommender-shared observation.

        Identical to `observe` except the observation does **not** enter
        the agent's pull history: `history` records the agent's own pulls
        only (which is what the last-k criterion and the simulator's
        history arrays are defined over). Used by the evidence-sharing
        recommender of interpretation 1.
        """
        if arm not in (ARM_A, ARM_B):
            raise ValueError(f"arm must be ARM_A or ARM_B; got {arm}")
        if outcome not in (0, 1):
            raise ValueError(f"outcome must be 0 or 1; got {outcome}")
        if outcome == 1:
            self.alpha_beta[arm, 0] += 1.0
        else:
            self.alpha_beta[arm, 1] += 1.0

    def apply_recommendation(self, recommendation: Recommendation) -> None:
        """Fold a recommendation into the posterior by explicit conditioning.

        The paper's §3 protocol says the agent first conditions on history
        (already done by `observe`) and then conditions on R_i^t before
        choosing. That second step requires a likelihood
        P(R | arm, history, posterior, Z) — supplied by the recommender on
        `Recommendation.likelihood` — and would be applied here as a Bayes
        update on the per-arm posterior.

        Neither Phase 2 recommender uses this route: evidence sharing
        updates via `observe_shared`, and the choice nudge bypasses beliefs
        entirely. Raising keeps the explicit-conditioning route honest
        until someone implements it.
        """
        raise NotImplementedError(
            "Explicit Bayesian conditioning on R is not implemented; "
            "use EvidenceSharingRecommender or ChoiceNudgeRecommender."
        )
