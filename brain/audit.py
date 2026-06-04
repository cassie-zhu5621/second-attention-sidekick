"""
audit.py — dimension audit on cached VLM scores (no API, numpy only).

Answers, with data: (1) does each dimension have RANGE (or is it floored/ceilinged)?
(2) which dimensions are REDUNDANT (highly correlated)? (3) how many independent
FACTORS are really there (PCA on the correlation matrix)? (4) how do the dimensions
map onto the theory groups (Berlyne / Kaplan / craft / narrative)?

Usage:
  python audit.py /path/to/scores_cache.json
"""
import sys, json
import numpy as np

# theory grouping for the writeup (Berlyne-anchored framework)
GROUP = {
    "novelty": "Berlyne", "conflict": "Berlyne", "tension": "Berlyne", "surprise": "Berlyne",
    "complexity": "Berlyne/Kaplan", "mystery": "Kaplan", "coherence": "Kaplan", "legibility": "Kaplan",
    "aesthetic": "craft", "color_harmony": "craft", "decisive_moment": "craft", "frame_within_frame": "craft",
    "story": "narrative", "story_potential": "narrative",
}


def load(path):
    d = json.load(open(path))
    dims = sorted({k for v in d.values() if isinstance(v, dict) for k in v})
    rows, names = [], []
    for fname, v in d.items():
        if isinstance(v, dict) and all(isinstance(v.get(x), (int, float)) for x in dims):
            rows.append([float(v[x]) for x in dims]); names.append(fname)
    X = np.array(rows)
    # auto-normalize if it looks like a 0-10 scale
    if X.max() > 1.5:
        X = X / 10.0
    return X, dims, names


def main():
    path = sys.argv[1]
    X, dims, names = load(path)
    n, d = X.shape
    print(f"Loaded {n} images x {d} dimensions from {path}\n")

    print("=== 1. RANGE per dimension (floored/ceilinged dims can't be validated here) ===")
    print(f"{'dim':20s} {'group':14s} {'mean':>6s} {'std':>6s} {'min':>6s} {'max':>6s}  flag")
    for j, dim in enumerate(dims):
        col = X[:, j]
        flag = ""
        if col.std() < 0.12: flag = "LOW RANGE"
        if col.mean() < 0.18: flag += " FLOORED"
        if col.mean() > 0.82: flag += " CEILING"
        print(f"{dim:20s} {GROUP.get(dim,'?'):14s} {col.mean():6.2f} {col.std():6.2f} "
              f"{col.min():6.2f} {col.max():6.2f}  {flag}")

    print("\n=== 2. CORRELATION matrix (redundancy: |r|>0.7 = measuring the same thing) ===")
    C = np.corrcoef(X.T)
    hdr = "".join(f"{dim[:6]:>7s}" for dim in dims)
    print(" " * 20 + hdr)
    for i, dim in enumerate(dims):
        print(f"{dim:20s}" + "".join(f"{C[i,j]:7.2f}" for j in range(d)))
    print("\n  redundant pairs (|r|>0.7):")
    found = False
    for i in range(d):
        for j in range(i + 1, d):
            if abs(C[i, j]) > 0.7:
                print(f"    {dims[i]} ~ {dims[j]}  r={C[i,j]:.2f}  -> consider merging"); found = True
    if not found: print("    none — dimensions are reasonably distinct")

    print("\n=== 3. FACTOR structure (PCA on correlation matrix; Kaiser: eigenvalue>1) ===")
    eig, vecs = np.linalg.eigh(C)
    order = np.argsort(eig)[::-1]; eig = eig[order]; vecs = vecs[:, order]
    var = eig / eig.sum()
    nfac = int((eig > 1).sum())
    print(f"  eigenvalues: {np.round(eig,2)}")
    print(f"  variance explained: {np.round(var*100,1)} %")
    print(f"  -> ~{nfac} independent factors (so {d} prompts may collapse to {nfac})")
    print("  top loadings per retained factor:")
    for f in range(max(1, nfac)):
        load_f = vecs[:, f]
        top = sorted(zip(dims, load_f), key=lambda t: abs(t[1]), reverse=True)[:3]
        print(f"    factor {f+1} ({var[f]*100:.0f}%): " + ", ".join(f"{nm}({v:+.2f})" for nm, v in top))

    print("\n=== takeaway ===")
    print("  Keep dims with range + distinct factor loadings; merge redundant pairs;")
    print("  dims that are FLOORED here are likely a CORPUS gap (not useless) — re-check on lab data.")


if __name__ == "__main__":
    main()
