"""Sanity tests for the Phase-1 recommenders model.

These do not test correctness of the paper's claims — they test that
the implementation behaves consistently with its own contracts:

- Bandit validates inputs.
- Agent's posterior updates are conjugate-correct.
- A myopic Bayesian agent eventually prefers the better arm, given
  enough evidence.
- The simulation orchestrator is reproducible under a fixed seed.
- The three discovery definitions return bools and respect the
  better-arm asymmetry on canonical histories.
"""

from __future__ import annotations

import numpy as np
import pytest

from model.agent import BetaBernoulliAgent
from model.bandit import ARM_A, ARM_B, BernoulliBandit
from model.discovery import (
    discovered_by_last_k,
    discovered_by_posterior_gap,
    discovered_by_posterior_probability,
)
from model.recommender import NullRecommender
from model.simulation import run_simulation


# ---------- bandit ----------------------------------------------------------


def test_bandit_validates_probabilities():
    with pytest.raises(ValueError):
        BernoulliBandit(p_a=1.1, p_b=0.5)
    with pytest.raises(ValueError):
        BernoulliBandit(p_a=0.5, p_b=0.0)
    with pytest.raises(ValueError):
        BernoulliBandit(p_a=0.4, p_b=0.6)  # p_a must exceed p_b
    with pytest.raises(ValueError):
        BernoulliBandit(p_a=0.5, p_b=0.5)  # strict inequality


def test_bandit_pull_respects_means():
    bandit = BernoulliBandit(p_a=0.9, p_b=0.1)
    rng = np.random.default_rng(0)
    n = 5000
    arms = np.array([ARM_A] * n + [ARM_B] * n)
    out = bandit.pull_many(arms, rng)
    p_a_hat = out[:n].mean()
    p_b_hat = out[n:].mean()
    assert abs(p_a_hat - 0.9) < 0.02
    assert abs(p_b_hat - 0.1) < 0.02


# ---------- agent -----------------------------------------------------------


def test_agent_default_prior_is_uniform_and_unbiased():
    agent = BetaBernoulliAgent(agent_id=0)
    assert np.allclose(agent.alpha_beta, np.array([[1.0, 1.0], [1.0, 1.0]]))
    assert np.allclose(agent.posterior_means, np.array([0.5, 0.5]))


def test_agent_conjugate_update():
    agent = BetaBernoulliAgent(agent_id=0)
    agent.observe(ARM_A, 1)  # success on A
    agent.observe(ARM_A, 0)  # failure on A
    agent.observe(ARM_B, 1)  # success on B
    assert np.allclose(agent.alpha_beta[ARM_A], [2.0, 2.0])
    assert np.allclose(agent.alpha_beta[ARM_B], [2.0, 1.0])
    assert agent.history.shape == (3, 2)
    assert agent.history.tolist() == [
        [ARM_A, 1],
        [ARM_A, 0],
        [ARM_B, 1],
    ]


def test_agent_rejects_bad_observations():
    agent = BetaBernoulliAgent(agent_id=0)
    with pytest.raises(ValueError):
        agent.observe(2, 1)
    with pytest.raises(ValueError):
        agent.observe(ARM_A, 2)


def test_agent_breaks_ties_randomly_at_uniform_prior():
    agent = BetaBernoulliAgent(agent_id=0)
    rng = np.random.default_rng(42)
    picks = [agent.choose_arm(rng) for _ in range(200)]
    counts = np.bincount(picks, minlength=2)
    # Both arms should appear, neither dominantly. Tolerance generous.
    assert counts[ARM_A] > 50 and counts[ARM_B] > 50


def test_agent_prefers_arm_with_higher_posterior_mean():
    agent = BetaBernoulliAgent(
        agent_id=0,
        prior_alpha_beta=np.array([[10.0, 2.0], [2.0, 10.0]]),
    )
    rng = np.random.default_rng(0)
    # Posterior means: A = 10/12 ≈ 0.83, B = 2/12 ≈ 0.17.
    picks = [agent.choose_arm(rng) for _ in range(50)]
    assert all(p == ARM_A for p in picks)


def test_agent_recommendation_hook_is_phase2():
    """NullRecommender returns None → hook never invoked. A non-None
    recommendation would raise NotImplementedError (Phase 2 work)."""
    from model.recommender import Recommendation

    agent = BetaBernoulliAgent(agent_id=0)
    rng = np.random.default_rng(0)
    # Passing None is fine — Phase 1 happy path.
    agent.choose_arm(rng, recommendation=None)
    # Passing a real Recommendation is explicitly NOT supported yet.
    with pytest.raises(NotImplementedError):
        agent.choose_arm(rng, recommendation=Recommendation(arm=ARM_A))


# ---------- discovery -------------------------------------------------------


def test_discovery_last_k_short_history_is_false():
    history = np.array([[ARM_A, 1]] * 5, dtype=np.int64)
    assert discovered_by_last_k(history, np.eye(2), k=20) is False


def test_discovery_last_k_all_A_is_true():
    history = np.array([[ARM_A, 1]] * 20, dtype=np.int64)
    assert discovered_by_last_k(history, np.eye(2), k=20) is True


def test_discovery_last_k_recent_B_is_false():
    history = np.array(
        [[ARM_A, 1]] * 19 + [[ARM_B, 0]],
        dtype=np.int64,
    )
    assert discovered_by_last_k(history, np.eye(2), k=20) is False


def test_discovery_posterior_gap():
    # Posterior strongly favors A.
    ab = np.array([[20.0, 2.0], [2.0, 20.0]])
    assert discovered_by_posterior_gap(np.empty((0, 2)), ab, delta=0.05) is True
    # Posterior favors B; should be False.
    ab_bad = np.array([[2.0, 20.0], [20.0, 2.0]])
    assert discovered_by_posterior_gap(np.empty((0, 2)), ab_bad, delta=0.05) is False


def test_discovery_posterior_probability():
    ab = np.array([[20.0, 2.0], [2.0, 20.0]])
    rng = np.random.default_rng(0)
    assert (
        discovered_by_posterior_probability(
            np.empty((0, 2)), ab, threshold=0.95, n_samples=5000, rng=rng
        )
        is True
    )
    ab_uncertain = np.array([[5.0, 5.0], [5.0, 5.0]])
    assert (
        discovered_by_posterior_probability(
            np.empty((0, 2)), ab_uncertain, threshold=0.95, n_samples=5000, rng=rng
        )
        is False
    )


# ---------- simulation ------------------------------------------------------


def test_simulation_shapes_and_types():
    bandit = BernoulliBandit(p_a=0.7, p_b=0.4)
    result = run_simulation(bandit, n_agents=10, n_steps=50, seed=123)
    assert result.histories.shape == (10, 50, 2)
    assert result.final_alpha_beta.shape == (10, 2, 2)
    # alpha + beta should have grown by exactly n_steps per agent across arms.
    growth = result.final_alpha_beta.sum(axis=(1, 2)) - 4.0  # 4 = sum of Beta(1,1)×2
    assert np.all(growth == 50)


def test_simulation_is_reproducible_under_seed():
    bandit = BernoulliBandit(p_a=0.7, p_b=0.4)
    r1 = run_simulation(bandit, n_agents=5, n_steps=30, seed=7)
    r2 = run_simulation(bandit, n_agents=5, n_steps=30, seed=7)
    assert np.array_equal(r1.histories, r2.histories)
    assert np.array_equal(r1.final_alpha_beta, r2.final_alpha_beta)


def test_simulation_default_uses_null_recommender():
    """NullRecommender is the Phase-1 default — no exception, agents
    pull and observe normally."""
    bandit = BernoulliBandit(p_a=0.7, p_b=0.4)
    result = run_simulation(
        bandit, n_agents=3, n_steps=20, recommender=NullRecommender(), seed=1
    )
    assert result.histories.shape == (3, 20, 2)


def test_simulation_validates_args():
    bandit = BernoulliBandit(p_a=0.7, p_b=0.4)
    with pytest.raises(ValueError):
        run_simulation(bandit, n_agents=0, n_steps=10)
    with pytest.raises(ValueError):
        run_simulation(bandit, n_agents=2, n_steps=0)


def test_long_run_concentrates_posterior_on_better_arm():
    """With enough steps and a clear gap, a myopic Bayesian agent's
    posterior mean for A should exceed that for B."""
    bandit = BernoulliBandit(p_a=0.8, p_b=0.2)
    result = run_simulation(bandit, n_agents=20, n_steps=300, seed=2026)
    means = result.final_alpha_beta[..., 0] / result.final_alpha_beta.sum(axis=-1)
    share_correct = float(np.mean(means[:, ARM_A] > means[:, ARM_B]))
    # With p_a=0.8 vs p_b=0.2 and T=300, well over half of agents should
    # have settled on A. Loose threshold — we are not testing statistics here.
    assert share_correct >= 0.7
