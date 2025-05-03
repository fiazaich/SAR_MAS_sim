import matplotlib.pyplot as plt
from matplotlib import rcParams, rc


# ── 1. Style tweaks ────────────────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-paper')
plt.rc('font',      family='serif', size=10)
plt.rc('mathtext',  fontset='dejavuserif')
plt.rc('axes',      titlesize=14, labelsize=11)
plt.rc('xtick',     labelsize=10)
plt.rc('ytick',     labelsize=10)
plt.rc('legend',    fontsize=9)

def export_figure(filename="causal.pdf"):
    # Physical size: fits 3.33-inch IEEE column
    rcParams["figure.figsize"] = (3.33, 2.2)   # width, height in inches
    rcParams["figure.dpi"] = 100               # dpi irrelevant for PDF
    rcParams["pdf.fonttype"] = 42              # embed TrueType
    rc("font", family="serif")                 # Computer Modern
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight") 

# ── 2. Event data ─────────────────────────────────────────────────────────────
events = [
    ("Search Agent", 0.0, "Survivor detected\n(search 1)",  "C0"),
    ("Relay Agent",  2.2, "Relay activated\n(relay 1)",     "C2"),
    ("Rescue Agent", 2.5, "Rescue initiated\n(rescue 20)",  "C1"),
]
roles = ["Search Agent", "Relay Agent", "Rescue Agent"]
y_map = {r: i for i, r in enumerate(roles)}

# ── 3. Figure / axes ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.8, 3.6))       # slightly wider
ax.set_facecolor("white")
ax.set_xlim(-0.4, 3.6)
ax.set_ylim(-0.6, len(roles) - 0.4)
ax.invert_yaxis()

# ── light separators ─────────────────────────────────────────────────────────
for y in range(len(roles)):
    ax.hlines(y, -0.4, 3.6, lw=0.4, color="gray", alpha=0.25)

# ── 4. Points + labels ────────────────────────────────────────────────────────
for role, t, label, col in events:
    y = y_map[role]
    ax.scatter(t, y, s=60, color=col, edgecolor="k", zorder=4)

    # offset label by 10 pt right & 6 pt up (no collisions)
    ax.annotate(label,
                xy=(t, y),              # anchor at the dot
                xytext=(40, 20),        # 0 pt sideways, 15 pt up
                textcoords="offset points",
                ha="center", va="top",
                fontsize=9,
                zorder=3)      

# ── 5. Arrows between events ─────────────────────────────────────────────────
for (r1, t1, *_), (r2, t2, *_) in zip(events, events[1:]):
    ax.annotate("",
        xy=(t2, y_map[r2]), xytext=(t1, y_map[r1]),
        arrowprops=dict(arrowstyle="-|>", lw=1.1, color="k",
                        shrinkA=7, shrinkB=7))

# ── 6. Axes cosmetics ────────────────────────────────────────────────────────
ax.set_yticks(range(len(roles)))
ax.set_yticklabels(roles, fontweight="semibold")
ax.set_xlabel("Relative time (s from detection)", labelpad=6)
ax.set_title("Causal timeline for Zone A coordination", pad=8)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("gray")

plt.tight_layout()
export_figure()
plt.show()

