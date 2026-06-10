"""Recommender interface and the two Phase 2 operationalisations.

The paper introduces the recommender in §3 as a function

    R_i^t = rho(h_i^t, pi_i^t, Z)  in  {A, B}

taking an agent's private history, their current posterior, and a
*common* latent state Z (shared across all agents per simulation) and
returning a recommendation for the next pull.

Phase 2 implements two operationalisations of rho, mirroring §3 of the
paper:

- `EvidenceSharingRecommender` — interpretation 1: the recommender is a
  distinguished agent with a directed edge to every user, sharing labeled
  *sampled data*; the agent folds each shared observation into its Beta
  posterior by the ordinary conjugate update.
- `ChoiceNudgeRecommender` — interpretation 2: R_i^t is (probabilistically)
  the agent's actual next pull; Bayesian conditioning on R is abstracted
  away into a Z-dependent behavioural nudge.

Both carry the latent state Z in {Z_GOOD, Z_FAIL}. The `z_mode` switch
controls its scope: `'community'` draws Z once per simulation (the common
state that correlates agents — the paper's mechanism), `'per_share'`
re-flips Z on every recommendation (independent errors — the control
condition, and the frequentist reading of P(Z=G) as a long-run rate).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from .bandit import ARM_A, ARM_B

if TYPE_CHECKING:
    from .bandit import BernoulliBandit

# Latent recommender states: good and failure.
Z_GOOD = "G"
Z_FAIL = "F"


@dataclass(frozen=True)
class Recommendation:
    """A single recommendation handed to one agent at one step.

    `arm` is the recommended arm (`ARM_A` or `ARM_B`). The optional fields
    select how the agent consumes it (see `BetaBernoulliAgent.choose_arm`):

    - `outcome` set — a shared observation: `arm` is the label under which
      the recommender reports a Bernoulli draw `outcome`; the agent performs
      the conjugate update on that arm's posterior (interpretation 1).
    - `follow_prob` set — a behavioural nudge: the agent pulls `arm` with
      probability `follow_prob` and otherwise chooses myopically, with no
      belief update on R (interpretation 2).
    - `likelihood` set — P(R = arm | hidden truth, history, posterior, Z),
      the quantity needed for full Bayesian conditioning on R. Reserved for
      the explicit-conditioning route; not used by either Phase 2
      recommender.
    """

    arm: int
    likelihood: Optional[float] = None
    outcome: Optional[int] = None
    follow_prob: Optional[float] = None


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


class _LatentStateRecommender(Recommender):
    """Shared Z machinery for the two Phase 2 recommenders.

    Parameters
    ----------
    p_good : float
        P(Z = Z_GOOD). The paper's running value is 0.99.
    z_mode : {'community', 'per_share'}
        'community' draws Z once (lazily, on the first recommendation,
        with the recommender's RNG) and holds it for the whole simulation —
        the common state behind the §6 correlation mechanism. 'per_share'
        re-flips Z on every recommendation, making the recommender's errors
        independent across agents and steps — the control condition.
    """

    def __init__(self, p_good: float = 0.99, z_mode: str = "community") -> None:
        if not 0.0 <= p_good <= 1.0:
            raise ValueError(f"p_good must be in [0, 1]; got {p_good}")
        if z_mode not in ("community", "per_share"):
            raise ValueError(f"z_mode must be 'community' or 'per_share'; got {z_mode!r}")
        self.p_good = p_good
        self.z_mode = z_mode
        # The community draw, cached on first use; stays None in per_share
        # mode (there is no single Z to report) and is copied onto
        # `SimulationResult.z` by `run_simulation`.
        self.z: Optional[str] = None

    def _current_z(self, rng: np.random.Generator) -> str:
        if self.z_mode == "per_share":
            return Z_GOOD if rng.random() < self.p_good else Z_FAIL
        if self.z is None:
            self.z = Z_GOOD if rng.random() < self.p_good else Z_FAIL
        return self.z


class EvidenceSharingRecommender(_LatentStateRecommender):
    """Interpretation 1: a distinguished agent sharing sampled data.

    Each step, for each agent, the recommender pulls the true bandit and
    shares the draw as a labeled observation `(arm, outcome)`; the agent
    folds it into its Beta posterior by the ordinary conjugate update
    (beliefs only — shared data does not enter the agent's pull history).
    Draws are i.i.d. across agents given Z, so the only common cause the
    recommender injects is Z itself.

    Two variants of what Z does:

    - `variant='state_arm'` — Z selects the source: in Z_GOOD the
      recommender samples and truthfully labels the better arm A, in
      Z_FAIL the worse arm B. Labels are always honest. Note that honest
      data from either arm pins that arm's posterior near its true mean,
      which weakly *helps* discovery — this variant's failure state is
      not expected to suppress q.
    - `variant='confused'` — the recommender is a tutor sampling both arms
      (alternating by step). In Z_GOOD labels are correct; in Z_FAIL the
      two arms' identities are swapped, so draws from B are reported as A
      and vice versa. Beliefs get pinned at the wrong arms' rates, the
      posterior gap converges to -(p_A - p_B), and discovery is suppressed.
    """

    def __init__(
        self,
        bandit: "BernoulliBandit",
        p_good: float = 0.99,
        z_mode: str = "community",
        variant: str = "confused",
    ) -> None:
        super().__init__(p_good=p_good, z_mode=z_mode)
        if variant not in ("state_arm", "confused"):
            raise ValueError(f"variant must be 'state_arm' or 'confused'; got {variant!r}")
        self.bandit = bandit
        self.variant = variant

    def recommend(
        self,
        agent_id: int,
        history: np.ndarray,
        posterior_alpha_beta: np.ndarray,
        rng: np.random.Generator,
    ) -> Optional[Recommendation]:
        z = self._current_z(rng)
        if self.variant == "state_arm":
            source = ARM_A if z == Z_GOOD else ARM_B
            label = source
        else:  # 'confused'
            source = ARM_A if history.shape[0] % 2 == 0 else ARM_B
            if z == Z_GOOD:
                label = source
            else:
                label = ARM_B if source == ARM_A else ARM_A
        outcome = self.bandit.pull(source, rng)
        return Recommendation(arm=label, outcome=int(outcome))


class ChoiceNudgeRecommender(_LatentStateRecommender):
    """Interpretation 2: R_i^t is (probabilistically) the agent's next pull.

    Bayesian conditioning on R is abstracted away into a behavioural
    accuracy shift: in Z_GOOD the recommender points at the better arm A,
    in Z_FAIL at the worse arm B, and the agent pulls the pointed arm with
    probability `follow_prob`, choosing myopically otherwise. No belief
    update on R takes place; beliefs change only through the (honest)
    payoffs of whatever arm ends up pulled.
    """

    def __init__(
        self,
        p_good: float = 0.99,
        follow_prob: float = 0.1,
        z_mode: str = "community",
    ) -> None:
        super().__init__(p_good=p_good, z_mode=z_mode)
        if not 0.0 <= follow_prob <= 1.0:
            raise ValueError(f"follow_prob must be in [0, 1]; got {follow_prob}")
        self.follow_prob = follow_prob

    def recommend(
        self,
        agent_id: int,
        history: np.ndarray,
        posterior_alpha_beta: np.ndarray,
        rng: np.random.Generator,
    ) -> Optional[Recommendation]:
        z = self._current_z(rng)
        arm = ARM_A if z == Z_GOOD else ARM_B
        return Recommendation(arm=arm, follow_prob=self.follow_prob)
