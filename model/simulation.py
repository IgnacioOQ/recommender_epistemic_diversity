"""Simulation orchestrator.

Runs `n_agents` independent Beta-Bernoulli agents against a shared
`BernoulliBandit` for `n_steps` stages, optionally consulting a
`Recommender` before each pull. Phase 1's default `NullRecommender`
makes the simulation reduce to the unaided regime of §1-§2.

Per-step protocol per agent (matches §3 once the recommender is real):

  1. Ask the recommender for a recommendation given (history, posterior).
     Phase 1: always None.
  2. Agent chooses an arm (optionally folding the recommendation into
     its posterior first — Phase 2).
  3. Bandit returns a Bernoulli outcome on the chosen arm.
  4. Agent updates its posterior and appends to its history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.random import SeedSequence

from .agent import BetaBernoulliAgent
from .bandit import BernoulliBandit
from .recommender import NullRecommender, Recommender


@dataclass
class SimulationResult:
    """Frozen result of one simulation run.

    Attributes
    ----------
    bandit : BernoulliBandit
        The bandit the simulation ran against.
    histories : np.ndarray, shape (n_agents, n_steps, 2)
        Per-agent histories; row `t` is `[arm_pulled, outcome]`.
    final_alpha_beta : np.ndarray, shape (n_agents, 2, 2)
        Per-agent final Beta posteriors.
    seed : int
        The master seed used to derive per-agent seeds (see `run_simulation`).
    """

    bandit: BernoulliBandit
    histories: np.ndarray
    final_alpha_beta: np.ndarray
    seed: int

    @property
    def n_agents(self) -> int:
        return self.histories.shape[0]

    @property
    def n_steps(self) -> int:
        return self.histories.shape[1]


def run_simulation(
    bandit: BernoulliBandit,
    n_agents: int,
    n_steps: int,
    *,
    recommender: Optional[Recommender] = None,
    prior_alpha_beta: np.ndarray | None = None,
    seed: int | None = None,
) -> SimulationResult:
    """Run one simulation of `n_agents` independent agents.

    Parameters
    ----------
    bandit : BernoulliBandit
        The (shared) bandit instance.
    n_agents : int
        Number of agents.
    n_steps : int
        Number of stages each agent runs (T in the paper).
    recommender : Recommender, optional
        Defaults to `NullRecommender` (unaided regime).
    prior_alpha_beta : np.ndarray, shape (2, 2), optional
        Shared prior across all agents. Defaults to uniform Beta(1, 1)
        per arm.
    seed : int, optional
        Master seed. If `None`, drawn from OS entropy. Per-agent RNGs
        are spawned from this master via `SeedSequence.spawn` so different
        agents get statistically independent streams.

    Returns
    -------
    SimulationResult
    """
    if n_agents < 1:
        raise ValueError(f"n_agents must be >= 1; got {n_agents}")
    if n_steps < 1:
        raise ValueError(f"n_steps must be >= 1; got {n_steps}")

    if recommender is None:
        recommender = NullRecommender()
    if seed is None:
        seed = int(np.random.SeedSequence().entropy)  # type: ignore[arg-type]

    master_ss = SeedSequence(seed)
    # +1 for a separate stream the recommender can use across agents.
    child_seeds = master_ss.spawn(n_agents + 1)
    agent_rngs = [np.random.default_rng(s) for s in child_seeds[:n_agents]]
    recommender_rng = np.random.default_rng(child_seeds[n_agents])

    agents = [
        BetaBernoulliAgent(agent_id=i, prior_alpha_beta=prior_alpha_beta)
        for i in range(n_agents)
    ]

    histories = np.empty((n_agents, n_steps, 2), dtype=np.int64)

    for t in range(n_steps):
        for i, agent in enumerate(agents):
            recommendation = recommender.recommend(
                agent_id=i,
                history=histories[i, :t],
                posterior_alpha_beta=agent.alpha_beta,
                rng=recommender_rng,
            )
            arm = agent.choose_arm(agent_rngs[i], recommendation=recommendation)
            outcome = bandit.pull(arm, agent_rngs[i])
            agent.observe(arm, outcome)
            histories[i, t, 0] = arm
            histories[i, t, 1] = outcome

    final_alpha_beta = np.stack([a.alpha_beta for a in agents], axis=0)

    return SimulationResult(
        bandit=bandit,
        histories=histories,
        final_alpha_beta=final_alpha_beta,
        seed=seed,
    )
