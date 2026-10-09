"""
Shared constants/loaders for the judge v3 visualization prototypes
(build_judge_heatmap_prototype.py: task-level; build_judge_aggregate_heatmap_prototype.py:
aggregated-over-tasks). Kept separate from judge_common.py, which is about
producing judge v3 results, not visualizing them.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JUDGE_DIR = PROJECT_ROOT / "judge_v3_results"

AGENTS = ["vanilla", "aide", "mlevolve"]

# id -> (short label, full name, gate field or None). Order = display order:
# ungated modes first, then gated modes.
# F11 "Augment before split" dropped -- confirmed 0.0 across all 9 agent x
# model columns in judge_v3_results (verified 2026-09-17), pure dead weight
# in the legend/x-axis of every chart that reads this list.
# F20 "HPO w/o nested CV" dropped (2026-09-25, updated paper table -- 15
# modes now, not 16): too few applicable pipelines project-wide to carry its
# own column/row in any figure (this is the same reason
# build_judge_heatmap_table_by_agent.py had already excluded it from its own
# TAXONOMY_ORDER, pre-dating this removal -- now moot since it's gone from
# the base list too). Removing it here means FM_DISPLAY_ID's FM13-FM16 shift
# down to FM12-FM15 (see below) -- if F20 ever needs to come back, re-add
# ("F20", "HPO w/o nested CV", "hyperparameter_tuning") here AND restore its
# SEGMENT_COLORS entry at the same position AND shift FM12-FM15 back up.
FAILURE_MODES = [
    ("F03", "Test peeking", None),
    ("F04", "No cleaning", None),
    ("F09", "Scale before split", None),
    ("F10", "Feat-sel before split", None),
    ("F12", "Impute before split", None),
    ("F16", "Wrong model type", None),
    ("F26", "No val split", None),
    ("F31", "One metric only", None),
    ("F_TASKFORM", "Wrong task formulation", None),
    ("F_FEATENG", "No feature eng.", None),
    # F13 "Subject overlap" dropped by explicit request (2026-09-23, table hand-edit) --
    # kept out of every figure/table sharing this list from here on. If it needs to come
    # back, re-add ("F13", "Subject overlap", "has_subject_id_column") AND restore its
    # SEGMENT_COLORS entry below at the same position -- both lists are indexed
    # positionally against each other by build_judge_stacked_bar_mpl.py /
    # build_judge_stacked_bar_prototype.py (SEGMENT_COLORS[i] for FAILURE_MODES[i]).
    ("F14", "Ignores temporal order", "has_temporal"),
    ("F21", "No DL regularization", "used_deep_learning"),
    ("F27", "Reuses test across variants", "model_comparison"),
    ("F29", "Single eval, stochastic model", "uses_stochastic_model"),
    ("F_ENSEMBLE", "Naive ensembling", "ensembling"),
]
FM_IDS = [fid for fid, _, _ in FAILURE_MODES]

# key must match judge_common.MODEL_RUN_DIRS keys. "label" is the DISPLAY name (what
# actually appears in figures/tables) -- shortened to drop "-flash" by the same request
# that renamed Vanilla -> ReAct below; "key" stays the full form since it's also the
# on-disk directory name under judge_v3_results/<agent>/<key>/ (result_dir()) and must
# keep matching that regardless of how the label is written.
# Labels shortened + capitalization made consistent (2026-09-24, explicit request):
# every label now leads with a capital letter (gemini-3.x -> Gemini-3.x, matching
# Qwen's existing capital Q), and the Qwen labels drop their version number
# (qwen3.5-4b -> Qwen-4B, qwen3.8-27b -> Qwen-27B) since the size suffix alone
# already distinguishes them and the shorter form reads better in a table column.
MODELS = [
    {"key": "gemini-3.6-flash", "label": "Gemini-3.6"},
    {"key": "gemini-3.7-flash", "label": "Gemini-3.7"},
    {"key": "qwen3.5-4b", "label": "Qwen-4B"},
    # Added 2026-09-24: OpenRouter-backed qwen-3.8-27b sweep, judged tonight
    # (judge_v3_results/<agent>/qwen3.8-27b/, via result_dir()'s generic
    # <agent>/<model> subdir case below -- same pattern as qwen3.5-4b).
    {"key": "qwen3.8-27b", "label": "Qwen-27B"},
]

# Display name for each agent id -- AGENTS itself stays lowercase (it's also the
# judge_v3_results/<agent>/ directory name, result_dir()'s key, dsts_runs/<agent>/, etc.,
# so renaming the id itself would be a much larger, riskier change with no real benefit).
# "vanilla" -> "ReAct" per explicit request (2026-09-23): the zero-shot-with-retries loop
# this id has always referred to is described as ReAct-style in the paper, so that's now
# its display name everywhere -- AIDE/MLEvolve are already capitalized correctly and don't
# need remapping, but are listed here too so callers have one single lookup table instead
# of a per-script capitalize()/if-else.
AGENT_DISPLAY = {"vanilla": "ReAct", "aide": "AIDE", "mlevolve": "MLEvolve"}

COLUMNS = [(agent, m["key"], m["label"]) for agent in AGENTS for m in MODELS]

# Canonical paper-table numbering (FM01-FM15, pipeline-stage order) and
# leak/other category, layered on top of the ids in FAILURE_MODES without
# renaming them there -- those ids (== FM_IDS) are load-bearing: they're the
# literal JSON lookup key (fm.get(fid) in load_agent_model / every script
# below that reads judge_v3_results/*.json directly) AND get compared
# against each build_perf_vs_judge_effects*.py / analyze_*_vs_judge.py's own
# local LEAKAGE_MODES set (old-style codes, a narrower/differently-scoped
# "leakage" concept than the category below -- deliberately left alone).
# Renaming FAILURE_MODES's ids in place would silently break both without
# raising an error. FM_DISPLAY_ID / FM_LABEL / FM_CATEGORY are the
# reader-facing layer instead: swap a figure/table's rendered tick, legend,
# or row-header text to these wherever a human sees a failure-mode identity,
# leaving the underlying fid used for data lookups/statistics untouched.
#
# UPDATED 2026-09-25 (new paper table, 15 modes): F20/HPO dropped entirely
# (see FAILURE_MODES comment above) -- FM12-FM15 here are what were
# FM13-FM16 before that removal. Also F26 "No train/val split" flips
# category from "leak" to "other" per the new table (it was leak before).
# Everything else is unchanged from the prior table.
FM_DISPLAY_ID = {
    "F_TASKFORM": "FM01", "F03": "FM02", "F04": "FM03", "F12": "FM04",
    "F14": "FM05", "F26": "FM06", "F_FEATENG": "FM07", "F09": "FM08",
    "F10": "FM09", "F16": "FM10", "F21": "FM11",
    "F_ENSEMBLE": "FM12", "F27": "FM13", "F29": "FM14", "F31": "FM15",
}
FM_LABEL = {
    "F_TASKFORM": "Wrong task formulation",
    "F03": "Peeking at test data during EDA",
    "F04": "Not cleaning data",
    "F12": "Imputation before splitting",
    "F14": "Ignoring temporal order",
    "F26": "No train/val split",
    "F_FEATENG": "No feature engineering",
    "F09": "Scaling before splitting",
    "F10": "Feature selection before splitting",
    "F16": "Wrong model type for task",
    "F21": "No regularisation in DL",
    "F_ENSEMBLE": "Naive ensembling",
    "F27": "Reusing test set across variants",
    "F29": "Single eval of stochastic model",
    "F31": "Using only one eval metric",
}
FM_CATEGORY = {
    "F_TASKFORM": "other", "F03": "leak", "F04": "other", "F12": "leak",
    "F14": "leak", "F26": "other", "F_FEATENG": "other", "F09": "leak",
    "F10": "leak", "F16": "other", "F21": "other",
    "F_ENSEMBLE": "other", "F27": "leak", "F29": "other", "F31": "other",
}
# Same warm/cool convention build_perf_vs_judge_effects_barchart_rank.py
# already uses for its own leak-vs-other split (C_LEAK/C_OTHER).
CATEGORY_COLOR = {"leak": "#CD0324", "other": "#3468DC"}
# FM01..FM15 order, as the old-style ids FAILURE_MODES/FM_IDS still key on --
# matches build_judge_stacked_bar_by_agent.py's TAXONOMY_ORDER (independently
# derived from the same paper table's pipeline-stage grouping).
FM_DISPLAY_ORDER = ["F_TASKFORM", "F03", "F04", "F12", "F14", "F26",
                     "F_FEATENG", "F09", "F10", "F16", "F21",
                     "F_ENSEMBLE", "F27", "F29", "F31"]
assert set(FM_DISPLAY_ORDER) == set(FM_DISPLAY_ID) == set(FM_LABEL) == set(FM_CATEGORY) == set(FM_IDS)

# 15 modes (F13, F20 dropped, see above) + 1 "other" bucket for the free-form
# other_failure_modes catch-all. Pulled from matplotlib's tab20 (the 18 non-gray slots)
# rather than hand-picked -- tab20 is built for pairwise categorical distinguishability,
# which the earlier hand-picked hue-family palette didn't actually have (several
# near-duplicates: F03/F14, F09/F20, F10/F21, F11/F27, F13/F_FEATENG all read as the same
# color). Matters more here than in most charts since the static (matplotlib) version has
# no hover tooltip to rescue ambiguity -- color alone has to carry full identification.
# Three unused trailing tab20 slots now (F11's color was already unused before F13
# was dropped, and F20's own slot, "#f7b6d2", is now unused too since its removal) --
# harmless, just spare capacity.
SEGMENT_COLORS = [
    "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78",             # F03,F04,F09,F10
    "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5",  # F12,F16,F26,F31,F_TASKFORM
    "#8c564b",                                              # F_FEATENG
    "#e377c2", "#bcbd22", "#dbdb8d",                        # F14,F21,F27 (F13's own
                                                              # slot, "#c49c94", removed
                                                              # along with F13 above)
    "#17becf", "#9edae5",                                   # F29, F_ENSEMBLE
]
OTHER_COLOR = "#8a8f99"


def result_dir(agent: str, model: str) -> Path:
    # gemini-3.6-flash keeps the original flat layout (see run_judge_v3.py) --
    # everything else lives under its own model subdir.
    if model == "gemini-3.6-flash":
        return JUDGE_DIR / agent
    return JUDGE_DIR / agent / model


def cell_state(entry: dict) -> dict:
    if entry is None:
        return {"s": "missing"}
    if entry.get("applicable") is False:
        return {"s": "na"}
    present = entry.get("present")
    if present is True:
        return {
            "s": "present",
            "sev": entry.get("severity"),
            "reason": (entry.get("reasoning") or "")[:220],
            "evidence": (entry.get("evidence") or "")[:220],
        }
    if present is False:
        return {"s": "absent"}
    if present == "cannot_determine":
        return {"s": "cannot_determine", "reason": (entry.get("reasoning") or "")[:220]}
    return {"s": "missing"}


def load_agent_model(agent: str, model: str) -> dict:
    """task_id -> {cells: [cell_state per FM_IDS], no_code, other, stage_count, stage_count_max}"""
    tasks = {}
    d = result_dir(agent, model)
    if not d.exists():
        return tasks
    for path in sorted(d.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        fm = data.get("failure_modes", {})
        if not fm:
            continue  # parse_error entries have no failure_modes -- skip, not a judged result
        cells = [cell_state(fm.get(fid)) for fid in FM_IDS]
        applicable_cells = [c for c in cells if c["s"] != "na"]
        no_code = len(applicable_cells) > 0 and all(c["s"] == "cannot_determine" for c in applicable_cells)
        tasks[path.stem] = {
            "cells": cells,
            "no_code": no_code,
            "other": len(data.get("other_failure_modes", [])),
            "stage_count": data.get("stage_count"),
            "stage_count_max": data.get("stage_count_max"),
        }
    return tasks


def compute_taxonomy_column(agent: str, model: str) -> dict:
    """Average findings-per-task, decomposed by failure mode -- see
    build_judge_stacked_bar_prototype.py's docstring for why this
    (not stacked presence rates) is the statistically sound quantity here."""
    tasks = load_agent_model(agent, model)
    n_judged = sum(1 for t in tasks.values() if not t["no_code"])
    if n_judged == 0:
        return {"n_judged": 0, "segments": [0.0] * len(FAILURE_MODES), "other": 0.0, "n_nocode": len(tasks)}
    segments = []
    for i in range(len(FAILURE_MODES)):
        n_present = sum(1 for t in tasks.values() if not t["no_code"] and t["cells"][i]["s"] == "present")
        segments.append(n_present / n_judged)
    other_total = sum(t["other"] for t in tasks.values() if not t["no_code"])
    return {
        "n_judged": n_judged,
        "segments": segments,
        "other": other_total / n_judged,
        "n_nocode": sum(1 for t in tasks.values() if t["no_code"]),
    }


def compute_taxonomy_column_applicable(agent: str, model: str) -> dict:
    """Per-mode presence rate CONDITIONED on applicability (present / applicable),
    for a HEATMAP TABLE read as independent per-mode rates -- NOT for the stacked
    bar, which deliberately wants compute_taxonomy_column's present / n_judged (see
    that function's docstring: dividing every mode by the same n_judged is what
    makes the segments summable into one meaningful bar height).

    A heatmap cell doesn't carry that additivity constraint, so present / n_judged
    is the wrong choice there: it silently dilutes any GATED mode whenever its
    precondition is rare. E.g. F20 (HPO without nested CV, gated on
    hyperparameter_tuning) is applicable to only ~2% of pipelines project-wide --
    present / n_judged renders as near-0 in every cell even on a config where the
    failure fires on most of the few times HPO is even attempted, which reads to
    anyone scanning the table as "this basically never happens" when the truth is
    closer to "this is rarely relevant, but usually wrong when it is." present /
    applicable answers the question a heatmap cell is actually asked to answer:
    among pipelines where this mode COULD have occurred, how often did it.

    Returns n_applicable per mode alongside each rate (None where n_applicable==0)
    so callers can flag/suppress cells whose applicable pool is too small to
    trust -- see build_judge_heatmap_table_by_agent.py's MIN_APPLICABLE."""
    tasks = load_agent_model(agent, model)
    n_judged = sum(1 for t in tasks.values() if not t["no_code"])
    if n_judged == 0:
        return {"n_judged": 0, "n_applicable": [0] * len(FAILURE_MODES),
                "rates": [None] * len(FAILURE_MODES)}
    judged_tasks = [t for t in tasks.values() if not t["no_code"]]
    n_applicable = []
    rates = []
    for i in range(len(FAILURE_MODES)):
        applicable_cells = [t["cells"][i] for t in judged_tasks if t["cells"][i]["s"] != "na"]
        n_app = len(applicable_cells)
        n_pres = sum(1 for c in applicable_cells if c["s"] == "present")
        n_applicable.append(n_app)
        rates.append(n_pres / n_app if n_app else None)
    return {"n_judged": n_judged, "n_applicable": n_applicable, "rates": rates}
