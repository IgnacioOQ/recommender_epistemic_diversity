"""Three operational definitions of the discovery event D_i.

The paper introduces D_i (§1) as "agent i discovers which is the better
arm" and explicitly flags that it "needs to be defined rigorously
eventually". Until the paper picks one, we ship three candidates and
let the experiment notebook decide which (if any) yields the postulated
q ≈ 0.05 (§2).

All three operate post-hoc on an agent's final state. They take:

- `history`: shape `(T, 2)`, rows `[arm_pulled, outcome]`.
- `alpha_beta`: shape `(2, 2)`, the agent's final Beta parameters.

and return a bool. `True` means agent has discovered the better arm
(under the chosen definition).

Arm convention: `ARM_A = 0` is the better arm by construction
(see `bandit.py`).
"""

from __future__ import annotations

import numpy as np

from .bandit import ARM_A, ARM_B


def discovered_by_last_k(
    history: np.ndarray,
    alpha_beta: np.ndarray,  # noqa: ARG001 — unused; kept for uniform signature
    *,
    k: int = 20,
) -> bool:
    """Agent has pulled `ARM_A` on each of the last `k` steps.

    Operational reading: "the agent has settled on the right arm".
    Returns False if the agent has not yet taken `k` steps.
    """
    if history.shape[0] < k:
        return False
    return bool(np.all(history[-k:, 0] == ARM_A))


def discovered_by_posterior_gap(
    history: np.ndarray,  # noqa: ARG001 — unused; kept for uniform signature
    alpha_beta: np.ndarray,
    *,
    delta: float = 0.05,
) -> bool:
    """Posterior mean of `p_A` exceeds posterior mean of `p_B` by at least `delta`.

    Operational reading: "the agent's point estimate clearly favors A".
    """
    means = alpha_beta[:, 0] / alpha_beta.sum(axis=1)
    return bool(means[ARM_A] - means[ARM_B] >= delta)


def discovered_by_posterior_probability(
    history: np.ndarray,  # noqa: ARG001 — unused; kept for uniform signature
    alpha_beta: np.ndarray,
    *,
    threshold: float = 0.95,
    n_samples: int = 2000,
    rng: np.random.Generator | None = None,
) -> bool:
    """Monte-Carlo estimate of `P(p_A > p_B | history) >= threshold`.

    Operational reading: "the agent believes A is better with high
    posterior probability". Computed by sampling independently from the
    two Beta posteriors — this is exact in the limit of large `n_samples`.
    """
    if rng is None:
        rng = np.random.default_rng()
    alpha_a, beta_a = alpha_beta[ARM_A]
    alpha_b, beta_b = alpha_beta[ARM_B]
    samples_a = rng.beta(alpha_a, beta_a, size=n_samples)
    samples_b = rng.beta(alpha_b, beta_b, size=n_samples)
    prob_a_better = float(np.mean(samples_a > samples_b))
    return prob_a_better >= threshold
