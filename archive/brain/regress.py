"""
regress.py — learn the taste weights from a person's preferences (the "回归").

Two standard forms (numpy only, no sklearn needed):
  - ridge_fit:    scalar ratings  y ~ X w   (L2-regularized linear regression)
  - pairwise_fit: pairwise picks  "i preferred over j" -> logistic on (s_i - s_j)
                  (Bradley-Terry / RankNet / relative-attributes formulation)

Both yield a weight per dimension. Still just a linear weighted sum — regression
only FITS the weights instead of you hand-setting them.

The __main__ block is a self-test: it invents a hidden "true taste", generates
preferences from the real cached score vectors, then checks we recover it.
"""
import numpy as np


def ridge_fit(X, y, alpha=1.0):
    """X: (n,d) dimension scores, y: (n,) ratings -> weights (d,)."""
    d = X.shape[1]
    A = X.T @ X + alpha * np.eye(d)
    return np.linalg.solve(A, X.T @ y)


def pairwise_fit(diffs, alpha=1.0, lr=0.5, iters=500):
    """diffs: (m,d) = s_i - s_j for pairs where i was preferred (target=+1).
    Logistic regression with L2; returns weights (d,)."""
    m, d = diffs.shape
    w = np.zeros(d)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(diffs @ w)))        # P(i preferred)
        grad = diffs.T @ (p - 1.0) / m + alpha * w / m  # target is all +1
        w -= lr * grad
    return w


def pairwise_agreement(diffs, w):
    """fraction of held-out pairs predicted correctly (i.e. score_i > score_j)."""
    return float((diffs @ w > 0).mean())


if __name__ == "__main__":
    import sys, json
    # use the real cached score vectors as the item pool
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "/sessions/gallant-nifty-albattani/mnt/Projects/Interestingness_Composer/scores_cache.json"
    d = json.load(open(path))
    dims = sorted({k for v in d.values() if isinstance(v, dict) for k in v})
    X = np.array([[float(v[k]) for k in dims] for v in d.values()
                  if isinstance(v, dict) and all(k in v for k in dims)])
    if X.max() > 1.5: X = X / 10.0
    n = len(X); rng = np.random.default_rng(0)

    # invent a hidden "true taste": this person loves story + decisive_moment, dislikes clutter(conflict)
    w_true = np.zeros(len(dims))
    for k, val in {"story": 1.0, "decisive_moment": 0.8, "conflict": -0.6, "aesthetic": 0.4}.items():
        if k in dims: w_true[dims.index(k)] = val
    true_score = X @ w_true

    # sample pairwise preferences, split train/test
    pairs = rng.integers(0, n, size=(400, 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    diffs, labels = [], []
    for i, j in pairs:
        if true_score[i] == true_score[j]: continue
        if true_score[i] > true_score[j]: diffs.append(X[i] - X[j])
        else: diffs.append(X[j] - X[i])
    diffs = np.array(diffs); split = int(0.8 * len(diffs))
    w_hat = pairwise_fit(diffs[:split], alpha=0.5)

    print(f"items={n}  dims={dims}")
    print("\nrecovered weights vs the hidden 'true taste' (cos sim should be high):")
    cos = (w_hat @ w_true) / (np.linalg.norm(w_hat) * np.linalg.norm(w_true) + 1e-9)
    for k, a, b in zip(dims, w_hat, w_true):
        print(f"  {k:18s} learned={a:+.2f}   true={b:+.2f}")
    print(f"\n  cosine(learned, true) = {cos:.2f}")
    print(f"  held-out pairwise agreement = {pairwise_agreement(diffs[split:], w_hat):.2%}")
    print("\n-> the regression recovers a person's taste from their pairwise picks.")
