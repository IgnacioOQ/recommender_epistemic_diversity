# Reading notes — *The effects of AI recommendation on epistemic diversity*

Source: [latex/recommenders_v2.tex](latex/recommenders_v2.tex).

## §1 Standard two-armed bandit

- Arms $A, B$ with mean payoffs $p_A, p_B$; $p_A > p_B$.
- $n$ agents, **independent**, no communication, no shared observation.
- Each agent: Beta prior over each of $p_A, p_B$ (so two independent priors).
- Myopic Bayesian: each step pick the arm with higher posterior expected payoff.
- $D_i$ = "agent $i$ discovers the better arm" — **left undefined** (flagged
  as TODO by the author). Community success: $D = D_1 \cup \dots \cup D_n$.

## §2 Unaided collective success

- Stipulate $P(D_i) = q = 0.05$ for all $i$.
- Independence → $P(D) = 1 - (1-q)^n \approx 0.994$ for $n=100$.
- The $q=0.05$ figure is a *postulate* — not derived from the model.
  Empirically reproducing it pins down the discovery definition.

## §3 AI recommender

- Per stage $t$, agent $i$ hands the recommender her history $h_i^t$ and
  posterior $\pi_i^t$. The recommender returns $R_i^t = \rho(h_i^t, \pi_i^t, Z) \in \{A, B\}$.
- $Z \in \{G, F\}$ with $P(G) = 0.99$, $P(F) = 0.01$ — **common across all
  agents**. This is the source of cross-agent correlation.
- Aided protocol per step: (1) condition $\pi_i^t$ on history; (2) condition
  on $R_i^t$; (3) pick the arm with higher posterior expected payoff.
- The recommender is opaque — the paper does not yet pin down how $\rho$
  computes its recommendation given $(h, \pi, Z)$.

## §4 Conjectures

- $P(D_i \mid Z=G) = 0.1$, $P(D_i \mid Z=F) = 0$.
- Intuition: in $G$ the recommender nudges toward $A$ and raises discovery
  $0.05 \to 0.1$; in $F$ the recommender misleads with early $B$ recs and
  effectively eliminates discovery.

## §5 The headline result

- Marginal individual discovery: $0.99 \cdot 0.1 + 0.01 \cdot 0 = 0.099$
  (up from $0.05$ unaided).
- Community discovery (conditional on $Z=G$, independent across agents):
  $1 - 0.9^{100} \approx 0.99997$; conditional on $Z=F$, zero.
- Aided community discovery: $0.99 \cdot 0.99997 + 0.01 \cdot 0 \approx 0.98997$
  (**down** from $0.994$ unaided).

## §6 Mechanism

- Unaided: agents' bad-luck draws are independent → community averages out.
- Aided: a common $Z$ → bad-luck becomes correlated → community can't
  average out the failure case. **Epistemic diversity** drops because
  evidence streams now share a common source.
- Important: this is *not* a wheel network with AI as hub. The AI does
  not sample arms or generate payoffs.

## §7 Next steps (paper's own)

1. Pin down the model details and run simulations confirming §4–§5.
2. Add history-sharing networks and more sophisticated recommenders.

## Open modelling questions (for our codebase)

- **Definition of $D_i$.** Three candidates implemented in `model/discovery.py`:
  last-$k$-step choice, posterior-mean gap, posterior $P(p_A > p_B)$.
  Decide which one (if any) reproduces $q \approx 0.05$ under sensible
  defaults.
- **Recommender likelihood.** §3 leaves $\rho$'s functional form open.
  Phase 2 needs a concrete family — e.g. "in $G$, $R$ matches the
  better arm with probability $1 - \eta_G$; in $F$, $R = B$ with
  probability $1 - \eta_F$" — and an explicit likelihood
  $P(R \mid A, h, \pi, Z)$ so agents can do the conditioning step.
- **Bernoulli vs continuous payoffs.** The Beta-prior choice strongly
  hints at Bernoulli rewards (conjugacy). We assume Bernoulli throughout.
- **Number of stages $T$.** Not stated; needs to be long enough that
  $q$ stabilises. Sensitivity sweep in the notebook.
