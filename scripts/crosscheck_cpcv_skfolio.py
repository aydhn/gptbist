"""Capraz dogrulama: bist_signal_bot CPCV  vs  skfolio.CombinatorialPurgedCV.

skfolio OPSIYONEL ve repo bagimliligi DEGILDIR. Kurulu degilse mesaj yazip 0 ile cikar.
Kullanim (izole venv'de, repo koku cwd):
    PYTHONPATH=. python scripts/crosscheck_cpcv_skfolio.py [--md cikti.md]
"""
from __future__ import annotations

import argparse
import sys
from math import comb


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None, help="markdown tablo cikti dosyasi")
    args = ap.parse_args(argv)
    try:
        import skfolio  # noqa: F401
        from skfolio.model_selection import CombinatorialPurgedCV as SkCPCV
    except Exception:
        print("skfolio kurulu değil, atlandı")
        return 0

    import numpy as np
    import pandas as pd
    from bist_signal_bot.edge_validation.cv import CombinatorialPurgedCV as OurCPCV

    def run(n, g, k, p, e, our_emb_bars, label):
        t0 = pd.date_range("2020-01-01", periods=n, freq="D")
        t1 = t0 + pd.Timedelta(days=p)  # etiket ufku p bar -> p satir purge
        ours = OurCPCV(g, k, embargo_bars=our_emb_bars)
        our_s = list(ours.split(t0, t1))
        sk = SkCPCV(n_folds=g, n_test_folds=k, purged_size=p, embargo_size=e)
        sk_s = list(sk.split(np.zeros((n, 1))))
        fs = n // g
        # (c) test grup kumeleri (indeksten turetilir)
        def sk_groups(tests):
            return tuple(sorted({min(int(i) // fs, g - 1) for t in tests for i in t[:1]}))
        our_groups = [s[2] for s in our_s]
        sk_groups_l = [sk_groups(s[1]) for s in sk_s]
        groups_eq = our_groups == sk_groups_l
        # (e) test indeks esitligi
        test_eq = sum(np.array_equal(o[1], np.sort(np.concatenate(s[1]))) for o, s in zip(our_s, sk_s))
        # (d) train Jaccard
        jac = []
        for o, s in zip(our_s, sk_s):
            a, b = set(o[0].tolist()), set(s[0].tolist())
            u = len(a | b)
            jac.append(1.0 if u == 0 else len(a & b) / u)
        ident = sum(j == 1.0 for j in jac)
        # (b) path sayisi + yol esitligi
        sk_paths = {tuple(int(x) for x in sk.recombined_paths[:, j]) for j in range(sk.n_test_paths)}
        our_paths = {tuple(si for si, _ in pm) for pm in ours.path_map()}
        return {
            "senaryo": label, "N": n, "p": p, "e": e,
            "split(biz/sk)": f"{ours.n_splits}/{sk.n_splits} (C={comb(g, k)})",
            "path(biz/sk)": f"{ours.n_paths}/{sk.n_test_paths}",
            "yol_kumesi_esit": our_paths == sk_paths,
            "test_gruplari_esit": groups_eq,
            "test_idx_esit": f"{test_eq}/{len(our_s)}",
            "train_ozdes": f"{ident}/{len(jac)}",
            "jaccard_ort": round(float(np.mean(jac)), 4),
            "jaccard_min": round(float(np.min(jac)), 4),
        }

    rows = [
        run(600, 6, 2, 0, 0, 0, "A purge=0 embargo=0, N%6==0"),
        run(601, 6, 2, 0, 0, 0, "B purge=0 embargo=0, N%6!=0 (kalan)"),
        run(600, 6, 2, 5, 0, 0, "C purge=5 (biz: t1=t0+5, emb 0)"),
        run(600, 6, 2, 5, 3, 3, "D purge=5 embargo=3 (naif esleme)"),
        run(600, 6, 2, 5, 3, 8, "E purge=5 embargo=3 (biz emb_bars=p+e)"),
        run(450, 6, 2, 0, 4, 4, "F purge=0 embargo=4"),
    ]
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(df.to_markdown(index=False) if hasattr(df, "to_markdown") else df.to_string(index=False))
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
