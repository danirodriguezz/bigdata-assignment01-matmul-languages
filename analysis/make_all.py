#!/usr/bin/env python3
"""Regenerate every table, figure and number of the Assignment 1 report from results/raw/ alone.

Inputs (raw, never edited):  results/raw/size_sweep.csv, rss_baseline.csv, c_flags.csv,
                             size_sweep_skipped.csv (optional), correctness_tests.json
Outputs: results/summary/*.csv, report/figures/*.pdf|png, report/generated/*.tex (tables + numbers.tex)

Statistics: warm-up rows (is_warmup = 1) are excluded; median and IQR (Q3 - Q1, numpy linear
quantiles) over the k measured samples of each configuration; failed rows (status != ok) are
counted and reported, never given a time. No other exclusion rule is applied.

Usage:  .venv/bin/python analysis/make_all.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import summarize as S  # noqa: E402
from plot_style import new_figure, savefig  # noqa: E402

RAW = ROOT / "results" / "raw"
SUM = ROOT / "results" / "summary"
FIG = ROOT / "report" / "figures"
GEN = ROOT / "report" / "generated"
for d in (SUM, FIG, GEN):
    d.mkdir(parents=True, exist_ok=True)

LANGS = ["c", "java", "python"]
NAME = {"c": "C (gcc -O2)", "java": "Java (OpenJDK 21)", "python": "Python (CPython 3.12)"}
SHORT = {"c": "C", "java": "Java", "python": "Python"}
STYLE = {"c": ("#0072B2", "o", "-"), "java": ("#E69F00", "s", "--"), "python": ("#009E73", "^", "-.")}
FIT_MIN_N = 256          # growth fit range: n >= 256 (constant per-call overheads negligible)
RNG = np.random.default_rng(12345)
macros = {}


def macro(name, value):
    macros[name] = value


def fmt_s(x):
    """Format a time in seconds with 3 significant figures and a unit (LaTeX)."""
    if pd.isna(x):
        return "--"
    if x >= 1:
        return f"{x:.3g}\\,s" if x < 100 else f"{x:.0f}\\,s"
    if x >= 1e-3:
        return f"{x * 1e3:.3g}\\,ms"
    return f"{x * 1e6:.3g}\\,\\textmu s"


def g3(x):
    return f"{x:.3g}"


def boot_ratio_ci(a, b, reps=5000):
    """95% bootstrap CI of median(a)/median(b) (independent resampling of both samples)."""
    a, b = np.asarray(a), np.asarray(b)
    ra = np.median(RNG.choice(a, size=(reps, len(a))), axis=1)
    rb = np.median(RNG.choice(b, size=(reps, len(b))), axis=1)
    r = ra / rb
    return float(np.quantile(r, .025)), float(np.quantile(r, .975))


# ----------------------------------------------------------------------------- load
def load(paths):
    df = S.load(paths)
    for col in ("repetition", "loadavg_1m"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


sweep = load([RAW / "size_sweep.csv"])
measured = sweep[(sweep["is_warmup"] == 0)]
ok = measured[measured["status"] == "ok"].copy()
ok["ns_per_madd"] = ok["time_s"] / ok["n"] ** 3 * 1e9
ok["batch"] = ok["extra_json"].map(lambda s: json.loads(s).get("batch", 1) if s else 1)

group_cols = [c for c in S.CONFIG_COLS if c in sweep]
summary = S.summarise(sweep, group_cols)
summary["ns_per_madd_median"] = summary["median_s"] / summary["n"] ** 3 * 1e9
summary = summary.sort_values(["language", "n"])
summary.to_csv(SUM / "summary_size_sweep.csv", index=False)
lim = S.limits(summary, group_cols)

skipped_path = RAW / "size_sweep_skipped.csv"
skipped = pd.read_csv(skipped_path) if skipped_path.exists() else pd.DataFrame(columns=["language", "n", "reason"])

# ----------------------------------------------------------------------------- limits
attempted = measured.groupby("language")["n"].max()
rows = []
for lang in LANGS:
    s = summary[summary.language == lang]
    done = s[(s.n_ok > 0) & (s.n_failed == 0)]
    fail = s[s.n_failed > 0]
    sk = skipped[skipped.language == lang]
    lf = int(done.n.max()) if len(done) else np.nan
    rows.append({"language": lang, "largest_completed_n": lf,
                 "largest_attempted_n": int(attempted.get(lang, np.nan)),
                 "failed_n": ";".join(str(int(x)) for x in fail.n) or "",
                 "failure_type": ";".join(sorted(set(";".join(fail.failed_statuses).split(";")) - {""})),
                 "not_attempted_n": ";".join(str(int(x)) for x in sk.n) or ""})
limits = pd.DataFrame(rows)
limits.to_csv(SUM / "limits.csv", index=False)
for _, r in limits.iterrows():
    macro(f"MaxN{SHORT[r.language]}", f"{r.largest_completed_n}")
    macro(f"MaxAttN{SHORT[r.language]}", f"{r.largest_attempted_n}")

# ----------------------------------------------------------------------------- runtime table
tab = summary.pivot(index="n", columns="language")
lines = [r"\begin{table*}[t]", r"\centering",
         r"\caption{Kernel runtime per multiplication: median and interquartile range (IQR) over $k$ measured samples "
         r"(warm-ups excluded), time per multiply--add $T/n^3$, and median peak resident set size (RSS, GNU \texttt{time}) "
         r"of the whole process. Timer boundary: kernel only. ``--'': not run (see \cref{tab:limits}).}",
         r"\label{tab:runtime}", r"\footnotesize", r"\setlength{\tabcolsep}{3.5pt}",
         r"\begin{tabular}{@{}r" + "rrrrr" * 3 + r"@{}}", r"\toprule",
         " & " + " & ".join(rf"\multicolumn{{5}}{{c}}{{{NAME[l]}}}" for l in LANGS) + r" \\",
         r"\cmidrule(lr){2-6}\cmidrule(lr){7-11}\cmidrule(l){12-16}",
         r"$n$" + r" & Median & IQR & $k$ & ns/madd & RSS [MiB]" * 3 + r" \\", r"\midrule"]
for n in sorted(summary.n.unique()):
    cells = [str(int(n))]
    for lang in LANGS:
        r = summary[(summary.language == lang) & (summary.n == n)]
        if len(r) == 0:
            cells += ["--"] * 5
            continue
        r = r.iloc[0]
        if r.n_ok == 0:
            cells += [rf"\multicolumn{{4}}{{c}}{{{r.failed_statuses} ($>600$\,s)}}", "--"]
            continue
        cells += [fmt_s(r.median_s), fmt_s(r.iqr_s), str(int(r.n_ok)), f"{r.ns_per_madd_median:.2f}",
                  f"{r.median_peak_rss_mib:.1f}"]
    lines.append(" & ".join(cells) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
(GEN / "table_runtime.tex").write_text("\n".join(lines) + "\n")

# ----------------------------------------------------------------------------- growth fit
fit_rows = []
for lang in LANGS:
    for lo, hi, tag in ((FIT_MIN_N, 10**9, "main"), (64, 512, "small"), (512, 10**9, "large")):
        s = summary[(summary.language == lang) & (summary.n_ok > 0) & (summary.n >= lo) & (summary.n <= hi)]
        if len(s) < 3:
            continue
        x, y = np.log(s.n.to_numpy(float)), np.log(s.median_s.to_numpy(float))
        (b, a), cov = np.polyfit(x, y, 1, cov=True)
        se = float(np.sqrt(cov[0, 0]))
        from scipy import stats
        half = float(stats.t.ppf(0.975, len(s) - 2)) * se
        r2 = 1 - np.sum((y - (a + b * x)) ** 2) / np.sum((y - y.mean()) ** 2)
        fit_rows.append({"language": lang, "range": tag, "n_min": int(s.n.min()), "n_max": int(s.n.max()),
                         "points": len(s), "exponent_b": b, "ci95_low": b - half, "ci95_high": b + half, "r2": r2})
fits = pd.DataFrame(fit_rows)
fits.to_csv(SUM / "growth_fit.csv", index=False)
for _, r in fits.iterrows():
    tag = {"main": "", "small": "Small", "large": "Large"}[r.range]
    p = f"Exp{tag}{SHORT[r.language]}"
    macro(p, f"{r.exponent_b:.2f}")
    macro(p + "Lo", f"{r.ci95_low:.2f}")
    macro(p + "Hi", f"{r.ci95_high:.2f}")
    macro(p + "Nmin", str(r.n_min))
    macro(p + "Nmax", str(r.n_max))
lines = [r"\begin{table}[t]", r"\centering",
         r"\caption{Empirical growth exponent $b$ of $T \approx c\,n^b$ (least squares on $\log$ median runtime vs.\ $\log n$) "
         r"with 95\,\% confidence interval (Student $t$ on the slope). The cubic model predicts $b=3$.}",
         r"\label{tab:growth}", r"\small", r"\begin{tabular}{@{}llrcc@{}}", r"\toprule",
         r"Implementation & $n$ range & pts & $b$ [95\,\% CI] & $R^2$ \\", r"\midrule"]
for _, r in fits.iterrows():
    lines.append(f"{SHORT[r.language]} & {r.n_min}--{r.n_max} & {r.points} & "
                 f"{r.exponent_b:.2f} [{r.ci95_low:.2f}, {r.ci95_high:.2f}] & {r.r2:.4f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(GEN / "table_growth.tex").write_text("\n".join(lines) + "\n")

# ----------------------------------------------------------------------------- ratios
ratio_rows = []
for n in sorted(ok.n.unique()):
    tc = ok[(ok.language == "c") & (ok.n == n)].time_s.to_numpy()
    for lang in ("java", "python"):
        tl = ok[(ok.language == lang) & (ok.n == n)].time_s.to_numpy()
        if len(tc) == 0 or len(tl) == 0:
            continue
        lo, hi = boot_ratio_ci(tl, tc) if len(tl) > 1 and len(tc) > 1 else (np.nan, np.nan)
        ratio_rows.append({"n": int(n), "language": lang, "k_lang": len(tl), "k_c": len(tc),
                           "ratio_median": np.median(tl) / np.median(tc), "ci95_low": lo, "ci95_high": hi})
ratios = pd.DataFrame(ratio_rows)
ratios.to_csv(SUM / "ratios_vs_c.csv", index=False)
for lang in ("java", "python"):
    r = ratios[ratios.language == lang]
    macro(f"Ratio{SHORT[lang]}Min", f"{r.ratio_median.min():.3g}")
    macro(f"Ratio{SHORT[lang]}Max", f"{r.ratio_median.max():.3g}")
    macro(f"Ratio{SHORT[lang]}MinN", str(int(r.loc[r.ratio_median.idxmin(), 'n'])))
    macro(f"Ratio{SHORT[lang]}MaxN", str(int(r.loc[r.ratio_median.idxmax(), 'n'])))
    for _, rr in r.iterrows():
        nn = {64: "SixtyFour", 128: "OneTwoEight", 256: "TwoFiftySix", 384: "ThreeEightyFour",
              512: "FiveTwelve", 768: "SevenSixtyEight", 1024: "TenTwentyFour", 1536: "FifteenThirtySix",
              2048: "TwentyFortyEight"}[rr.n]
        macro(f"Ratio{SHORT[lang]}{nn}", f"{rr.ratio_median:.3g}")
        macro(f"Ratio{SHORT[lang]}{nn}Lo", f"{rr.ci95_low:.3g}")
        macro(f"Ratio{SHORT[lang]}{nn}Hi", f"{rr.ci95_high:.3g}")

NWORD = {64: "SixtyFour", 128: "OneTwoEight", 256: "TwoFiftySix", 384: "ThreeEightyFour", 512: "FiveTwelve",
         768: "SevenSixtyEight", 1024: "TenTwentyFour", 1536: "FifteenThirtySix", 2048: "TwentyFortyEight"}
for _, r in summary[summary.n_ok > 0].iterrows():
    p = f"T{SHORT[r.language]}{NWORD[int(r.n)]}"
    macro(p, fmt_s(r.median_s))
    macro(p + "IQR", fmt_s(r.iqr_s))
    macro(p + "K", str(int(r.n_ok)))
    macro(f"NsMadd{SHORT[r.language]}{NWORD[int(r.n)]}", f"{r.ns_per_madd_median:.3g}")
    macro(f"Rss{SHORT[r.language]}{NWORD[int(r.n)]}", f"{r.median_peak_rss_mib:.1f}")
for lang in LANGS:
    s = summary[(summary.language == lang) & (summary.n_ok > 0)]
    macro(f"NsMadd{SHORT[lang]}Min", f"{s.ns_per_madd_median.min():.3g}")
    macro(f"NsMadd{SHORT[lang]}Max", f"{s.ns_per_madd_median.max():.3g}")
    macro(f"NsMadd{SHORT[lang]}MinN", str(int(s.loc[s.ns_per_madd_median.idxmin(), "n"])))
    macro(f"NsMadd{SHORT[lang]}MaxN", str(int(s.loc[s.ns_per_madd_median.idxmax(), "n"])))
    rel = (s.iqr_s / s.median_s)
    macro(f"RelIQR{SHORT[lang]}Max", f"{100 * rel.max():.1f}")
    macro(f"RelIQR{SHORT[lang]}MaxN", str(int(s.loc[rel.idxmax(), "n"])))
    macro(f"RelIQR{SHORT[lang]}Median", f"{100 * rel.median():.1f}")

# ----------------------------------------------------------------------------- checksums / bit identity
cs = ok.groupby(["n", "language"])["checksum"].agg(lambda v: set(v.astype(str)))
ident = []
for n in sorted(ok.n.unique()):
    sets = [cs.get((n, l)) for l in LANGS if (n, l) in cs.index]
    union = set().union(*sets)
    # C prints %.17g, Java/Python print the shortest repr: compare as float64 values
    vals = {float(v) for v in union}
    ident.append({"n": int(n), "languages": len(sets), "distinct_checksum_values": len(vals)})
ident = pd.DataFrame(ident)
ident.to_csv(SUM / "checksum_consistency.csv", index=False)
macro("ChecksumAllIdentical", "yes" if (ident.distinct_checksum_values == 1).all() else "no")
macro("ChecksumSizes", str(len(ident)))

# ----------------------------------------------------------------------------- load average
macro("LoadMin", f"{ok.loadavg_1m.astype(float).min():.2f}")
macro("LoadMax", f"{ok.loadavg_1m.astype(float).max():.2f}")
macro("LoadMedian", f"{ok.loadavg_1m.astype(float).median():.2f}")
macro("NumRawRows", str(len(sweep)))
macro("NumMeasuredOk", str(len(ok)))
macro("NumWarmupRows", str(int((sweep.is_warmup == 1).sum())))
first_ts, last_ts = pd.to_datetime(sweep.timestamp).min(), pd.to_datetime(sweep.timestamp).max()
macro("SweepStart", first_ts.strftime("%Y-%m-%d %H:%M"))
macro("SweepEnd", last_ts.strftime("%H:%M"))
macro("SweepMachineMinutes", f"{sweep.drop_duplicates('run_id').process_wall_s.astype(float).sum() / 60:.0f}")

# Measurement sessions: the sweep was interrupted and resumed on another day. A new session starts
# when two consecutive raw rows are more than one hour apart. Load average is reported per session.
ts = pd.to_datetime(sweep.timestamp)
sess_id = (ts.sort_values().diff() > pd.Timedelta(hours=1)).cumsum().reindex(ts.index)
sweep["session"] = sess_id + 1
ok["session"] = sweep.loc[ok.index, "session"]
macro("NumSessions", str(int(sweep.session.max())))
sess_rows = []
for s_num, g in sweep.groupby("session"):
    word = {1: "One", 2: "Two", 3: "Three"}[int(s_num)]
    t = pd.to_datetime(g.timestamp)
    g_ok = ok[ok.session == s_num]
    macro(f"Session{word}Start", t.min().strftime("%Y-%m-%d %H:%M"))
    macro(f"Session{word}End", t.max().strftime("%H:%M"))
    macro(f"Session{word}LoadMedian", f"{g_ok.loadavg_1m.astype(float).median():.2f}")
    macro(f"Session{word}LoadMax", f"{g_ok.loadavg_1m.astype(float).max():.2f}")
    confs = sorted({(l, int(n)) for l, n in zip(g_ok.language, g_ok.n)})
    sess_rows.append({"session": int(s_num), "start": t.min(), "end": t.max(), "measured_rows": len(g_ok),
                      "load_median": g_ok.loadavg_1m.astype(float).median(),
                      "configurations": ";".join(f"{l}:{n}" for l, n in confs)})
pd.DataFrame(sess_rows).to_csv(SUM / "sessions.csv", index=False)
# configurations whose samples come from more than one session
mixed = ok.groupby(["language", "n"]).session.nunique()
mixed = mixed[mixed > 1]
for (lang, n), _ in mixed.items():
    p = f"Mixed{SHORT[lang]}{NWORD[int(n)]}"
    for s_num, g in ok[(ok.language == lang) & (ok.n == n)].groupby("session"):
        word = {1: "One", 2: "Two", 3: "Three"}[int(s_num)]
        macro(f"{p}Session{word}Median", fmt_s(g.time_s.median()))
        macro(f"{p}Session{word}K", str(len(g)))

# ----------------------------------------------------------------------------- figure 1: runtime vs n
fig, ax = new_figure(height=2.5)
for lang in LANGS:
    s = summary[(summary.language == lang) & (summary.n_ok > 0)]
    c, m, ls = STYLE[lang]
    ax.errorbar(s.n, s.median_s, yerr=[s.median_s - s.q1_s, s.q3_s - s.median_s], color=c, marker=m,
                linestyle=ls, label=NAME[lang], markersize=4)
    fail = summary[(summary.language == lang) & (summary.n_ok == 0)]
    for _, f in fail.iterrows():
        ax.plot([f.n], [600], marker="x", color=c, markersize=7, linestyle="none")
        ax.annotate(f"{SHORT[lang]} {f.failed_statuses}\n(600 s limit)", (f.n, 600), textcoords="offset points",
                    xytext=(-62, -4), fontsize=6, color="0.25")
# cubic reference line anchored at C, n = 256
c256 = summary[(summary.language == "c") & (summary.n == 256)].median_s.iloc[0]
xs = np.array([64, 2048])
ax.plot(xs, c256 * (xs / 256.0) ** 3, color="0.55", linestyle=":", linewidth=1, label=r"$\propto n^3$ (reference)")
ax.axhline(600, color="0.7", linewidth=0.6)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(sorted(summary.n.unique()))
ax.set_xticklabels([str(int(v)) for v in sorted(summary.n.unique())], rotation=45)
ax.minorticks_off()
ax.set_xlabel("Matrix size $n$")
ax.set_ylabel("Median kernel runtime [s]")
ax.legend(loc="upper left", frameon=False)
savefig(fig, FIG / "runtime_vs_n")

# ----------------------------------------------------------------------------- figure 2: ns per multiply-add
fig, axes = new_figure(height=2.6)
fig.clf()
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)
for lang in LANGS:
    s = ok[ok.language == lang]
    g = s.groupby("n").ns_per_madd
    med, q1, q3 = g.median(), g.quantile(.25), g.quantile(.75)
    c, m, ls = STYLE[lang]
    ax = ax2 if lang == "python" else ax1
    ax.errorbar(med.index, med, yerr=[med - q1, q3 - med], color=c, marker=m, linestyle=ls, label=NAME[lang],
                markersize=4)
for ax in (ax1, ax2):
    ax.set_xscale("log", base=2)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", frameon=False)
    ax.minorticks_off()
ax2.set_xticks(sorted(summary.n.unique()))
ax2.set_xticklabels([str(int(v)) for v in sorted(summary.n.unique())], rotation=45)
plt_setp = [lbl.set_visible(False) for lbl in ax1.get_xticklabels()]
ax2.set_xlabel("Matrix size $n$")
fig.supylabel("Time per multiply–add [ns]", fontsize=8, x=0.02)
savefig(fig, FIG / "ns_per_madd")

# ----------------------------------------------------------------------------- memory
base = load([RAW / "rss_baseline.csv"])
base_ok = base[(base.status == "ok") & (base.is_warmup == 0)]
base_rss = base_ok.groupby("language").peak_rss_kib.median() / 1024
for lang in LANGS:
    macro(f"RssBase{SHORT[lang]}", f"{base_rss[lang]:.1f}")
mem_rows = []
for _, r in summary[summary.n_ok > 0].iterrows():
    lang, n = r.language, int(r.n)
    rss_mib = r.median_peak_rss_mib
    dense = 3 * 8 * n * n / 2**20
    mem_rows.append({"language": lang, "n": n, "median_peak_rss_mib": rss_mib, "baseline_rss_mib": base_rss[lang],
                     "rss_minus_baseline_mib": rss_mib - base_rss[lang], "dense_storage_mib": dense,
                     "memory_metric": r.memory_metric, "lang_metric_mib": r.median_memory_mib,
                     "lang_metric_bytes_per_element": r.median_memory_mib * 2**20 / (3 * n * n)})
mem = pd.DataFrame(mem_rows)
mem.to_csv(SUM / "memory.csv", index=False)
for lang in LANGS:
    s = mem[mem.language == lang].sort_values("n")
    big = s.iloc[-1]
    macro(f"MemMetricBpe{SHORT[lang]}", f"{big.lang_metric_bytes_per_element:.1f}")
    macro(f"RssOverDense{SHORT[lang]}", f"{big.rss_minus_baseline_mib / big.dense_storage_mib:.2f}")
    macro(f"RssMaxN{SHORT[lang]}", f"{big.median_peak_rss_mib:.1f}")
    macro(f"RssMaxNn{SHORT[lang]}", str(int(big.n)))
# common size for memory comparison: the largest n that all three completed
common_n = int(mem.groupby("n").language.nunique().loc[lambda x: x == 3].index.max())
macro("MemCommonN", str(common_n))
for lang in LANGS:
    r = mem[(mem.language == lang) & (mem.n == common_n)].iloc[0]
    macro(f"RssCommon{SHORT[lang]}", f"{r.median_peak_rss_mib:.1f}")
    macro(f"RssNetCommon{SHORT[lang]}", f"{r.rss_minus_baseline_mib:.1f}")
macro("DenseCommon", f"{3 * 8 * common_n**2 / 2**20:.1f}")

fig, ax = new_figure(height=2.4)
for lang in LANGS:
    s = mem[mem.language == lang]
    c, m, ls = STYLE[lang]
    ax.plot(s.n, s.median_peak_rss_mib, color=c, marker=m, linestyle=ls, label=NAME[lang])
xs = np.array(sorted(summary.n.unique()), dtype=float)
ax.plot(xs, 3 * 8 * xs**2 / 2**20, color="0.4", linestyle=":", label=r"dense storage $3\cdot 8n^2$ B")
ax.plot(xs, 3 * 32 * xs**2 / 2**20, color="0.7", linestyle=":", label=r"$3\cdot 32n^2$ B (boxed floats)")
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(xs)
ax.set_xticklabels([str(int(v)) for v in xs], rotation=45)
ax.minorticks_off()
ax.set_xlabel("Matrix size $n$")
ax.set_ylabel("Median peak RSS [MiB]")
ax.legend(loc="upper left", frameon=False, fontsize=6)
savefig(fig, FIG / "memory_rss")

lines = [r"\begin{table}[t]", r"\centering",
         r"\caption{Memory at the largest completed $n$ of each implementation. Peak RSS: median over the measured "
         r"process runs (GNU \texttt{time} \%M); baseline: median peak RSS of the same program at $n=1$ ($k=5$). "
         r"Language metric: C \texttt{matrix\_storage\_bytes} (exact allocation), Java \texttt{jvm\_heap\_peak\_used\_bytes} "
         r"(MemoryPoolMXBean, heap pools), Python \texttt{pyobj\_deep\_size\_bytes} (\texttt{sys.getsizeof}). "
         r"The metrics measure different things and are not directly comparable.}",
         r"\label{tab:memory}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
         r"Impl. & $n$ & RSS & Baseline & RSS$-$base & $3\cdot8n^2$ & Lang. metric (B/elem.) \\",
         r" & & [MiB] & [MiB] & [MiB] & [MiB] & [MiB] \\", r"\midrule"]
for lang in LANGS:
    s = mem[mem.language == lang].sort_values("n")
    for _, r in pd.concat([s[s.n == common_n], s.iloc[[-1]]]).drop_duplicates("n").iterrows():
        lines.append(f"{SHORT[lang]} & {r.n} & {r.median_peak_rss_mib:.1f} & {r.baseline_rss_mib:.1f} & "
                     f"{r.rss_minus_baseline_mib:.1f} & {r.dense_storage_mib:.1f} & "
                     f"{r.lang_metric_mib:.1f} ({r.lang_metric_bytes_per_element:.1f}) \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(GEN / "table_memory.tex").write_text("\n".join(lines) + "\n")

# ----------------------------------------------------------------------------- Java JIT warm-up evidence
warm = sweep[(sweep.status == "ok") & (sweep.language == "java")].copy()
steady = ok[ok.language == "java"].groupby("n").time_s.median()
warm["rel"] = warm.apply(lambda r: r.time_s / steady.get(r.n, np.nan), axis=1)
w = warm[warm.is_warmup == 1].groupby(["n", "repetition"]).rel.median().reset_index()
w.to_csv(SUM / "java_warmup.csv", index=False)
first = w[w.repetition == 0].set_index("n").rel
macro("JavaFirstIterMaxRel", f"{first.max():.2g}")
macro("JavaFirstIterMaxRelN", str(int(first.idxmax())))
macro("JavaFirstIterLargeRel", f"{first.loc[first.index.max()]:.2g}")
macro("JavaFirstIterLargeN", str(int(first.index.max())))
for lang in ("c", "python"):
    wl = sweep[(sweep.status == "ok") & (sweep.language == lang)]
    st = ok[ok.language == lang].groupby("n").time_s.median()
    wf = wl[(wl.is_warmup == 1) & (wl.repetition == 0)].copy()
    wf["rel"] = wf.apply(lambda r: r.time_s / st.get(r.n, np.nan), axis=1)
    m = wf.groupby("n").rel.median()
    macro(f"{SHORT[lang]}FirstIterRelMax", f"{m.max():.2f}")
    macro(f"{SHORT[lang]}FirstIterRelMin", f"{m.min():.2f}")

fig, ax = new_figure(height=2.1)
cmap_ns = [n for n in (64, 256, 512, 1024, 2048) if n in w.n.unique()]
greys = ["#0072B2", "#56B4E9", "#E69F00", "#D55E00", "#000000"]
mk = ["o", "s", "^", "D", "v"]
for i, n in enumerate(cmap_ns):
    s = w[w.n == n].sort_values("repetition")
    xs = list(s.repetition + 1) + [s.repetition.max() + 2]
    ys = list(s.rel) + [1.0]
    ax.plot(xs, ys, marker=mk[i], color=greys[i], label=f"$n={n}$")
ax.axhline(1.0, color="0.6", linewidth=0.6)
ax.set_yscale("log")
ax.set_xlabel("In-process iteration (last point: measured steady-state sample)")
ax.set_ylabel("Time / median measured")
ax.set_xticks(range(1, 7))
ax.legend(frameon=False, ncol=3)
savefig(fig, FIG / "java_warmup")

# ----------------------------------------------------------------------------- limits table
lines = [r"\begin{table}[t]", r"\centering",
         r"\caption{Feasibility limits under the declared budgets (600\,s per process run, 8\,GB memory, "
         r"$\leq$\,90\,min total benchmark time).}",
         r"\label{tab:limits}", r"\small", r"\begin{tabular}{@{}lrrl@{}}", r"\toprule",
         r"Impl. & Largest completed $n$ & Largest attempted $n$ & Outcome above \\", r"\midrule"]
for _, r in limits.iterrows():
    out = []
    if r.failed_n:
        out.append(f"{r.failure_type} at $n={r.failed_n}$")
    if r.not_attempted_n:
        out.append(f"not attempted: $n={r.not_attempted_n}$")
    if not out:
        out.append("none (end of declared sequence)")
    lines.append(f"{SHORT[r.language]} & {r.largest_completed_n} & {r.largest_attempted_n} & {'; '.join(out)} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(GEN / "table_limits.tex").write_text("\n".join(lines) + "\n")
fail_py = summary[(summary.language == "python") & (summary.n_ok == 0)]
macro("PyFailN", str(int(fail_py.n.min())) if len(fail_py) else "none")
macro("PyFailType", fail_py.failed_statuses.iloc[0] if len(fail_py) else "none")
macro("PyFailWall", f"{measured[(measured.language == 'python') & (measured.status != 'ok')].process_wall_s.astype(float).max():.0f}"
      if len(fail_py) else "none")

# ----------------------------------------------------------------------------- correctness table
cor = json.loads((RAW / "correctness_tests.json").read_text())
rnd = [c for c in cor["cases"] if c["case"].startswith("random")]
macro("CorrectPassed", "all" if cor["passed"] else "NOT all")
macro("CorrectMaxErrOverBound", f"{max(c[k] for c in rnd for k in c if k.endswith('_over_bound')):.3f}")
macro("CorrectMaxAbsErr", f"{max(c[k] for c in rnd for k in c if k.endswith('_max_abs_err_vs_numpy')):.2e}".replace("e-", r"\times 10^{-") + "}")
macro("CorrectMaxRelErr", f"{max(c[k] for c in rnd for k in c if k.endswith('_max_rel_err_vs_numpy')):.2e}".replace("e-", r"\times 10^{-") + "}")
macro("CorrectNumCases", str(len(cor["cases"])))
macro("NumpyVersion", cor.get("numpy_version", ""))
lines = [r"\begin{table}[t]", r"\centering",
         r"\caption{Correctness tests (all implementations run through the benchmarked command-line programs). "
         r"``exact'': bit-wise equal to the expected matrix; error vs.\ NumPy: maximum absolute error and maximum ratio "
         r"to the bound $2nu(|A||B|)_{ij}$ (pass if $\leq 1$).}",
         r"\label{tab:correctness}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}lrlc@{}}", r"\toprule",
         r"Case & $n$ & Check (C, Java, Python) & Identical \\", r"\midrule"]
for c in cor["cases"]:
    name = c["case"].replace("_", r"\_")
    if c["case"].startswith("random"):
        e = max(c[k] for k in c if k.endswith("_max_abs_err_vs_numpy"))
        rb = max(c[k] for k in c if k.endswith("_over_bound"))
        chk = f"max err {e:.1e}, ratio {rb:.2f}"
    else:
        chk = "exact"
    same = all(v for k, v in c.items() if k.endswith("bit_identical_to_c"))
    lines.append(f"{name} & {c['n']} & {chk} & {'yes' if same else 'no'} \\\\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(GEN / "table_correctness.tex").write_text("\n".join(lines) + "\n")

# ----------------------------------------------------------------------------- C flags (separate experiment)
flags_path = RAW / "c_flags.csv"
if flags_path.exists():
    fl = load([flags_path])
    fs = S.summarise(fl, group_cols)
    fs.to_csv(SUM / "summary_c_flags.csv", index=False)
    order = ["naive_ijk_gcc-O0", "naive_ijk_gcc-O2", "naive_ijk_gcc-O3", "naive_ijk_gcc-O3_march_native"]
    label = {"naive_ijk_gcc-O0": "-O0", "naive_ijk_gcc-O2": "-O2", "naive_ijk_gcc-O3": "-O3",
             "naive_ijk_gcc-O3_march_native": "-O3 -march=native"}
    ns = sorted(fs.n.unique())
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Separate experiment (not part of the language comparison): same C source compiled with "
             r"different gcc flags. Median [IQR] kernel runtime, $k=5$ process runs, 1 warm-up each.}",
             r"\label{tab:cflags}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
             r"\begin{tabular}{@{}l" + "r" * len(ns) + r"@{}}", r"\toprule",
             "gcc flags & " + " & ".join(f"$n={int(n)}$" for n in ns) + r" \\", r"\midrule"]
    for mth in order:
        cells = [r"\texttt{" + label[mth] + "}"]
        for n in ns:
            r = fs[(fs.method == mth) & (fs.n == n)]
            cells.append("--" if len(r) == 0 or r.iloc[0].n_ok == 0 else
                         f"{fmt_s(r.iloc[0].median_s)} [{fmt_s(r.iloc[0].iqr_s)}]")
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (GEN / "table_cflags.tex").write_text("\n".join(lines) + "\n")
    fok = fl[(fl.status == "ok") & (fl.is_warmup == 0)]
    nmax = max(ns)
    med = fok[fok.n == nmax].groupby("method").time_s.median()
    macro("CflagsN", str(int(nmax)))
    macro("CflagsOzeroOverOtwo", f"{med['naive_ijk_gcc-O0'] / med['naive_ijk_gcc-O2']:.3g}")
    macro("CflagsOthreeOverOtwo", f"{med['naive_ijk_gcc-O3'] / med['naive_ijk_gcc-O2']:.3g}")
    macro("CflagsNativeOverOtwo", f"{med['naive_ijk_gcc-O3_march_native'] / med['naive_ijk_gcc-O2']:.3g}")
    csum = fok.groupby("n").checksum.agg(lambda v: len({float(x) for x in v}))
    macro("CflagsChecksumIdentical", "yes" if (csum == 1).all() else "no")

# ----------------------------------------------------------------------------- numbers.tex
out = ["% Generated by analysis/make_all.py from results/raw/ -- do not edit by hand."]
for k in sorted(macros):
    out.append(f"\\newcommand{{\\{k}}}{{{macros[k]}}}")
(GEN / "numbers.tex").write_text("\n".join(out) + "\n")
pd.Series(macros).to_csv(SUM / "numbers.csv", header=["value"])
print(f"summary: {len(summary)} configurations; {len(macros)} macros -> {GEN / 'numbers.tex'}")
print(limits.to_string(index=False))
print(fits.to_string(index=False))
