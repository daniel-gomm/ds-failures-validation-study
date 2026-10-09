"""
Human-annotation validity study: side-by-side (a) what the LLM judge saw and
(b) the 15-failure-mode checklist, for an annotator to independently assess
each of the 30 sampled pipelines (see sample_pipelines.py). Agreement between
these annotations and judge_verdicts_hidden.json (NOT loaded here -- see that
file's own docstring note) is computed afterward, outside this app.

Left column: the "judge_context" block is EXACTLY what judge_common.
build_task_context() assembled for the real judge_v3 prompt (task_id, the
bare "description" string -- confirmed to always equal task_id, see
sample_pipelines.py's docstring --, task_type/target/metric, extracted
structural facts, final code, process log). The "extra_context" block below
it (task.json metadata, description.md prose, a real data preview) is
labeled and visually separated as NOT shown to the LLM judge -- included
so a human has enough grounding to assess data-dependent failure modes at
all, but kept distinguishable so "annotator saw more context" doesn't get
silently conflated with "annotator caught a real miss".

Right column: one radio per failure mode (FM01-FM15 order, full name +
definition from judge_v3_spec.py), no pre-selected default (forces an
active choice), plus a free-text notes field.

Annotations persist to annotations.json (keyed by "<annotator>__<pipeline_id>"
so multiple annotators can share this file without collisions), written on
every "Save" click -- re-running/reopening the app resumes from whatever is
already saved for the entered annotator name.

Usage: streamlit run scripts/validation_study/app.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from judge_v3_spec import FAILURE_MODES as SPEC_MODES  # noqa: E402
from judge_viz_common import FM_IDS, FM_DISPLAY_ID, FM_LABEL  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
PIPELINES_PATH = APP_DIR / "sampled_pipelines.json"
ANNOTATIONS_PATH = APP_DIR / "annotations.json"

VERDICT_OPTIONS = ["Present", "Absent", "N/A (not applicable to this pipeline)", "Unsure"]

# FM01..FM15 order (matches every paper figure/table using this taxonomy),
# each with its full name + definition straight from judge_v3_spec.py --
# the same wording the LLM judge itself was given for these 15 modes.
CHECKLIST = [
    {"display_id": FM_DISPLAY_ID[fid], "fid": fid, "name": FM_LABEL[fid],
     "definition": SPEC_MODES[fid]["definition"]}
    for fid in sorted(FM_IDS, key=lambda f: FM_DISPLAY_ID[f])
]


@st.cache_data
def load_pipelines():
    return json.loads(PIPELINES_PATH.read_text())


def load_annotations() -> dict:
    if ANNOTATIONS_PATH.exists():
        return json.loads(ANNOTATIONS_PATH.read_text())
    return {}


def save_annotation(annotator: str, pipeline_id: str, verdicts: dict, notes: str):
    data = load_annotations()
    key = f"{annotator}__{pipeline_id}"
    data[key] = {
        "annotator": annotator,
        "pipeline_id": pipeline_id,
        "verdicts": verdicts,
        "notes": notes,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    ANNOTATIONS_PATH.write_text(json.dumps(data, indent=2))


st.set_page_config(page_title="Judge Validation Study", layout="wide")

pipelines = load_pipelines()

# --- Sidebar: annotator identity + navigation -------------------------------
with st.sidebar:
    st.header("Annotator")
    annotator = st.text_input("Your name / initials", key="annotator_name").strip()

    if not annotator:
        st.info("Enter your name to begin.")
        st.stop()

    all_annotations = load_annotations()
    done_ids = {
        v["pipeline_id"] for k, v in all_annotations.items()
        if v["annotator"] == annotator
    }

    st.markdown(f"**Progress: {len(done_ids)} / {len(pipelines)}**")
    st.progress(len(done_ids) / len(pipelines) if pipelines else 0)

    # Hosted deployments (e.g. Streamlit Community Cloud) don't have durable
    # local storage -- a container restart after enough idle time silently
    # discards anything written to annotations.json since the last git push.
    # This button lets an annotator (or whoever manages the deployment) save
    # a real backup on demand rather than relying on the server's disk.
    st.download_button(
        "Download annotations.json (backup)",
        data=ANNOTATIONS_PATH.read_text() if ANNOTATIONS_PATH.exists() else "{}",
        file_name="annotations.json",
        mime="application/json",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Pipelines")
    labels = [
        f"{'✅' if p['pipeline_id'] in done_ids else '⬜'} {p['pipeline_id']}"
        for p in pipelines
    ]
    if "idx" not in st.session_state:
        # Resume at the first not-yet-annotated pipeline for this annotator.
        first_unseen = next((i for i, p in enumerate(pipelines) if p["pipeline_id"] not in done_ids), 0)
        st.session_state.idx = first_unseen
    choice = st.radio("Jump to:", options=list(range(len(pipelines))),
                       format_func=lambda i: labels[i], index=st.session_state.idx, label_visibility="collapsed")
    st.session_state.idx = choice

idx = st.session_state.idx
pipeline = pipelines[idx]
pid = pipeline["pipeline_id"]
ctx = pipeline["judge_context"]
extra = pipeline["extra_context"]

st.title("LLM-Judge Validation Study")
st.caption(f"Pipeline {idx + 1} / {len(pipelines)} — **{pid}**  "
           f"(agent=`{pipeline['agent']}`, model=`{pipeline['model']}`, task=`{pipeline['task_id']}`)")

col_left, col_right = st.columns([1.1, 1])

# --- LEFT: what the judge saw, + extra human-only context ------------------
with col_left:
    st.subheader("What the LLM judge was shown")

    st.markdown(f"""
- **Task ID:** `{ctx['task_id']}`
- **Description (verbatim, as given to the judge):** `{ctx['description']}`
- **Task type:** {ctx['task_type']}
- **Target column:** `{ctx['target_column']}`
- **Metric:** {ctx['metric']} ({ctx['metric_direction']} is better)
- **Dataset facts:** has_temporal={ctx['dataset_facts'].get('has_temporal')}, \
has_subject_id_column={ctx['dataset_facts'].get('has_subject_id_column')}
""")

    with st.expander("Final code solution", expanded=True):
        st.code(ctx["code"], language="python", line_numbers=True)

    with st.expander("Process log (reasoning/search trace, last ~6000 chars)", expanded=False):
        st.text(ctx["process_log"])

    st.divider()
    st.warning(
        "Everything below this line was **NOT** shown to the LLM judge. It's included "
        "so you have enough grounding to assess data-dependent failure modes — but weigh "
        "your annotation accordingly: a mismatch you can only see *because* of this extra "
        "context isn't necessarily something the judge model should be faulted for missing.",
        icon="⚠️",
    )

    tj = extra.get("task_json") or {}
    if tj:
        with st.expander("Full task metadata (task.json)", expanded=False):
            st.json(tj)

    if extra.get("description_md"):
        with st.expander("Dataset description (description.md)", expanded=True):
            st.markdown(extra["description_md"])

    dp = extra.get("data_preview") or {}
    if dp.get("available"):
        with st.expander(
            f"Train data preview ({dp['n_total_rows']} rows x {dp.get('n_total_cols', len(dp['columns']))} cols total, "
            f"showing first {len(dp['rows'])})",
            expanded=True,
        ):
            st.dataframe(dp["rows"], use_container_width=True)
    else:
        st.caption("(No data preview available for this task.)")

# --- RIGHT: annotation checklist --------------------------------------------
with col_right:
    st.subheader("Your annotation — 15 failure modes")

    existing = all_annotations.get(f"{annotator}__{pid}", {})
    existing_verdicts = existing.get("verdicts", {})
    existing_notes = existing.get("notes", "")

    verdicts = {}
    for item in CHECKLIST:
        fid, label, defn = item["fid"], item["name"], item["definition"]
        st.markdown(f"**{item['display_id']} — {label}**")
        st.caption(defn)
        prior = existing_verdicts.get(fid)
        prior_index = VERDICT_OPTIONS.index(prior) if prior in VERDICT_OPTIONS else None
        verdicts[fid] = st.radio(
            label=f"verdict_{fid}", options=VERDICT_OPTIONS, index=prior_index,
            key=f"radio_{pid}_{fid}", label_visibility="collapsed", horizontal=True,
        )
        st.markdown("")

    notes = st.text_area("General notes (optional)", value=existing_notes, key=f"notes_{pid}")

    unanswered = [item["display_id"] for item in CHECKLIST if verdicts[item["fid"]] is None]
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("💾 Save", type="primary", use_container_width=True):
            if unanswered:
                st.error(f"Missing a verdict for: {', '.join(unanswered)}")
            else:
                save_annotation(annotator, pid, verdicts, notes)
                st.success("Saved.")
                st.rerun()
    with col_b:
        if idx < len(pipelines) - 1:
            if st.button("Save & Next ➡️", use_container_width=True):
                if unanswered:
                    st.error(f"Missing a verdict for: {', '.join(unanswered)}")
                else:
                    save_annotation(annotator, pid, verdicts, notes)
                    st.session_state.idx = idx + 1
                    st.rerun()
