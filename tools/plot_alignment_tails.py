import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, rc
from itertools import cycle
import glob
import re

# === CONFIG ===
DELAY_GLOB = "alignment_delays_cp*.csv"
OUTPUT_PLOT = "alignment_tail_with_fits.pdf"
MIN_POINTS_FOR_FIT = 4

# === LOAD FILES ===
#delay_files = sorted(glob.glob(DELAY_GLOB), key=lambda f: float(re.findall(r"cp([\d.]+)", f)[0]))
delay_files = sorted(
    glob.glob(DELAY_GLOB),
    key=lambda f: float(re.findall(r"cp([0-9]+(?:\.[0-9]+)?)", f)[0])
)

all_tails = {}
lambda_fits = {}

empirical_styles = cycle([
    {"color": "tab:orange",  "linestyle": "-.",  "marker": "o"},
    {"color": "tab:blue", "linestyle": "--", "marker": "s",},
    {"color": "black","linestyle": ":",  "marker": "^"},
])
plt.style.use('seaborn-v0_8-paper')
plt.rc('font',      family='serif', size=10)
plt.rc('mathtext',  fontset='dejavuserif')
plt.rc('axes',      titlesize=14, labelsize=11)
plt.rc('xtick',     labelsize=10)
plt.rc('ytick',     labelsize=10)
plt.rc('legend',    fontsize=9)
plt.figure(figsize=(8, 6))


def export_figure(filename="convergence.pdf"):
    # Physical size: fits 3.33-inch IEEE column
    rcParams["figure.figsize"] = (3.33, 2.2)   # width, height in inches
    rcParams["figure.dpi"] = 100               # dpi irrelevant for PDF
    rcParams["pdf.fonttype"] = 42              # embed TrueType
    rc("font", family="serif")                 # Computer Modern
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight")


for file in delay_files:
    # Cleaner and stricter match: matches cp0.2, cp1.0
    match = re.search(r"cp([0-9]+(?:\.[0-9]+)?)\.csv$", file)
    if not match:
        continue
    cp = float(match.group(1))


    df = pd.read_csv(file)
    delays = df["delay"].dropna().astype(int).tolist()
    xs = np.array(sorted(set(delays)))
    ys = np.array([np.mean([d > x for d in delays]) for x in xs])
    all_tails[cp] = (xs, ys)

    # Filter out zero probabilities to avoid log(0)
    xs_fit = xs[ys > 0]
    ys_fit = ys[ys > 0]
    style = next(empirical_styles)
    if len(xs_fit) >= MIN_POINTS_FOR_FIT:
        log_ys = np.log(ys_fit)
        slope, _ = np.polyfit(xs_fit, log_ys, 1)
        lambda_fit = -slope
        lambda_fits[cp] = lambda_fit
        bound_ys = np.exp(-lambda_fit * xs_fit)
        plt.semilogy(xs_fit, bound_ys, linestyle=style["linestyle"], color='dimgray', linewidth=1.2, label=f"exp fit λ={lambda_fit:.2f} ($\\rho = {cp}$)")

    # Plot empirical tail
    style = next(empirical_styles)
    plt.semilogy(xs, ys, marker=style["marker"], color=style["color"], linestyle=style["linestyle"], 
    label = f"empirical ($\\rho = {cp}$)"
)

# === PLOT ===

plt.xlabel("Delay threshold $k$")
plt.ylabel("Pr(alignment delay > k)")
plt.title("Alignment Delay Tails with Fitted Exponential Bounds")
plt.grid(True, which='both', axis='y', linewidth=0.4, alpha=0.5)
plt.legend()
plt.tight_layout()
#plt.savefig(OUTPUT_PLOT, dpi=300)
export_figure(OUTPUT_PLOT)
print(f"[✓] Plot saved to {OUTPUT_PLOT}")
