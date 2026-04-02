"""
Satt Academy Admission Questions Dashboard

View and explore 37,000+ admission questions scraped from sattacademy.com
across 23 Bangladeshi universities.

Run: streamlit run dashboard/app.py
"""

import json
import os
import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "data-crawling", "data", "satt_academy_admission",
    "satt_academy_admission_questions.jsonl",
)

st.set_page_config(
    page_title="Satt Academy Question Bank",
    page_icon="📚",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    records = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    df = pd.DataFrame(records)

    # Clean up number field
    if "number" in df.columns:
        df["number"] = df["number"].astype(str).str.strip()

    # Pretty university names
    df["university_display"] = (
        df["university"]
        .str.replace("-", " ")
        .str.title()
        .str.replace("Bsmrstu", "BSMRSTU")
        .str.replace("Bsmrau", "BSMRAU")
        .str.replace("Buet", "BUET")
        .str.replace("Kuet", "KUET")
        .str.replace("Ruet", "RUET")
        .str.replace("Hstu", "HSTU")
        .str.replace("Mbstu", "MBSTU")
        .str.replace("Mat", "MAT")
        .str.replace("Dat", "DAT")
        .str.replace("Sust", "SUST")
        .str.replace("Nstu", "NSTU")
    )

    return df


df = load_data()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")

# University filter
universities = sorted(df["university_display"].unique())
selected_unis = st.sidebar.multiselect(
    "University",
    universities,
    default=[],
    placeholder="All universities",
)

# Year filter
years = sorted(df["exam_year"].dropna().unique(), reverse=True)
selected_years = st.sidebar.multiselect(
    "Year",
    years,
    default=[],
    placeholder="All years",
)

# Subject filter
subjects = sorted(df["subject"].dropna().unique())
selected_subjects = st.sidebar.multiselect(
    "Subject",
    subjects,
    default=[],
    placeholder="All subjects",
)

# Question type filter
selected_type = st.sidebar.radio(
    "Question Type",
    ["All", "MCQ", "Written"],
    horizontal=True,
)

# Search
search_query = st.sidebar.text_input("Search question text", "")

# Apply filters
filtered = df.copy()
if selected_unis:
    filtered = filtered[filtered["university_display"].isin(selected_unis)]
if selected_years:
    filtered = filtered[filtered["exam_year"].isin(selected_years)]
if selected_subjects:
    filtered = filtered[filtered["subject"].isin(selected_subjects)]
if selected_type == "MCQ":
    filtered = filtered[filtered["question_type"] == "mcq"]
elif selected_type == "Written":
    filtered = filtered[filtered["question_type"] == "written"]
if search_query:
    filtered = filtered[
        filtered["question_text"].str.contains(search_query, case=False, na=False)
    ]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📚 Satt Academy Admission Question Bank")
st.caption("Science TutorLM Data — scraped from sattacademy.com")

# Stats row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Questions", f"{len(df):,}")
col2.metric("Filtered", f"{len(filtered):,}")
col3.metric("Universities", df["university"].nunique())
col4.metric("Exams", df["exam_name"].nunique())

st.divider()


# ---------------------------------------------------------------------------
# Overview tab and Question browser tab
# ---------------------------------------------------------------------------
tab_overview, tab_browse, tab_exam = st.tabs(["Overview", "Browse Questions", "Browse by Exam"])


# ========================== OVERVIEW TAB ==========================
with tab_overview:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Questions per University")
        uni_counts = (
            filtered.groupby("university_display")
            .size()
            .sort_values(ascending=True)
            .reset_index(name="count")
        )
        st.bar_chart(uni_counts, x="university_display", y="count", horizontal=True, height=600)

    with col_right:
        st.subheader("Questions per Subject (Top 20)")
        subj_counts = (
            filtered.groupby("subject")
            .size()
            .sort_values(ascending=False)
            .head(20)
            .reset_index(name="count")
        )
        st.bar_chart(subj_counts, x="subject", y="count", height=600)

    st.subheader("Questions per Year")
    year_counts = (
        filtered.groupby("exam_year")
        .size()
        .sort_index()
        .reset_index(name="count")
    )
    st.bar_chart(year_counts, x="exam_year", y="count")

    st.subheader("MCQ vs Written")
    type_counts = filtered["question_type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    st.bar_chart(type_counts, x="type", y="count")

    # Data quality
    st.subheader("Data Quality")
    total = len(filtered)
    if total > 0:
        mcq_mask = filtered["question_type"] == "mcq"
        mcq_df = filtered[mcq_mask]
        has_answer = (mcq_df["correct_option_index"] >= 0).sum() if "correct_option_index" in mcq_df.columns else 0
        has_options = (mcq_df["options"].apply(lambda x: len(x) if isinstance(x, list) else 0) >= 4).sum()

        qcol1, qcol2, qcol3 = st.columns(3)
        qcol1.metric("MCQ Questions", f"{len(mcq_df):,}")
        qcol2.metric("With Correct Answer", f"{has_answer:,} ({has_answer/max(len(mcq_df),1)*100:.1f}%)")
        qcol3.metric("With 4 Options", f"{has_options:,} ({has_options/max(len(mcq_df),1)*100:.1f}%)")


# ========================== BROWSE TAB ==========================
with tab_browse:
    st.subheader(f"Questions ({len(filtered):,} results)")

    # Pagination
    page_size = st.selectbox("Questions per page", [10, 25, 50], index=0)
    total_pages = max(1, (len(filtered) - 1) // page_size + 1)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

    start = (page - 1) * page_size
    end = start + page_size
    page_df = filtered.iloc[start:end]

    st.caption(f"Showing {start+1}-{min(end, len(filtered))} of {len(filtered):,}")

    for _, row in page_df.iterrows():
        with st.container(border=True):
            # Header
            header_cols = st.columns([3, 1, 1])
            header_cols[0].markdown(f"**{row.get('university_display', '')}** — {row.get('exam_name', '')}")
            header_cols[1].caption(f"Year: {row.get('exam_year', 'N/A')}")
            header_cols[2].caption(f"Subject: {row.get('subject', 'N/A')}")

            # Question
            q_num = row.get("number", "")
            st.markdown(f"**Q{q_num}.** {row.get('question_text', '')}")

            # Options (MCQ)
            if row.get("question_type") == "mcq":
                options = row.get("options", [])
                correct_idx = row.get("correct_option_index", -1)
                if isinstance(options, list) and options:
                    for i, opt in enumerate(options):
                        if i == correct_idx:
                            st.markdown(f"  :green[**{chr(65+i)}) {opt}** ✅]")
                        else:
                            st.markdown(f"  {chr(65+i)}) {opt}")

            # Written answer
            if row.get("question_type") == "written":
                answer = row.get("answer_text", "")
                if answer:
                    with st.expander("Show Answer"):
                        st.write(answer)
                else:
                    st.caption("_(Written question — no answer text available)_")


# ========================== EXAM TAB ==========================
with tab_exam:
    st.subheader("Browse by Exam")

    # Exam selector
    exam_names = sorted(filtered["exam_name"].unique())
    selected_exam = st.selectbox("Select Exam", exam_names, index=0 if exam_names else None)

    if selected_exam:
        exam_df = filtered[filtered["exam_name"] == selected_exam]
        st.caption(f"{len(exam_df)} questions in this exam")

        # Group by subject within exam
        for subject, group in exam_df.groupby("subject"):
            st.markdown(f"### {subject}")
            for _, row in group.iterrows():
                q_num = row.get("number", "")
                q_text = row.get("question_text", "")
                options = row.get("options", [])
                correct_idx = row.get("correct_option_index", -1)

                with st.expander(f"Q{q_num}. {q_text[:100]}{'...' if len(q_text) > 100 else ''}"):
                    st.markdown(f"**{q_text}**")
                    if isinstance(options, list) and options:
                        for i, opt in enumerate(options):
                            if i == correct_idx:
                                st.markdown(f":green[**{chr(65+i)}) {opt}** ✅]")
                            else:
                                st.markdown(f"{chr(65+i)}) {opt}")

                    if row.get("question_type") == "written":
                        answer = row.get("answer_text", "")
                        if answer:
                            st.markdown(f"**Answer:** {answer}")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Data scraped from [sattacademy.com](https://sattacademy.com) for the "
    "Science TutorLM research project. 37,039 questions across 23 universities."
)
