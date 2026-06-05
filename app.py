# app.py
"""
Streamlit UI for data-confessions.
Multi-agent causal analysis system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from src.graph import get_data_summary
from src.prompts import (
    INVESTIGATOR_PROMPT, STATISTICIAN_PROMPT,
    CAUSAL_ANALYST_PROMPT, SKEPTIC_PROMPT, REPORTER_PROMPT
)

load_dotenv()

st.set_page_config(
    page_title="Data Confessions",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Data Confessions")
st.subheader("A Multi-Agent Causal Analysis System")
st.markdown("""
*Inspired by Everybody Lies and The Book of Why*  
This system analyzes **Chicago crime and weather data (2018–2023)** 
using 5 AI agents that investigate, quantify, reason causally, 
challenge, and report.
""")

st.divider()

# ── Question selector ──────────────────────────────────────────────────────────
SUGGESTED = [
    "Does rain reduce crime in Chicago?",
    "Does temperature predict crime better than rain?",
    "Are there more crimes on weekends than weekdays?",
    "Did crime patterns change after COVID lockdowns?",
    "Write your own question...",
]

selection = st.selectbox(
    "Choose a question or write your own:",
    SUGGESTED
)

if selection == "Write your own question...":
    question = st.text_input(
        "Your question:",
        placeholder="Ask a causal question about crime and weather in Chicago...",
    )
else:
    question = selection
    st.info(f"**Selected:** {question}")

run = st.button("Run Analysis", type="primary", disabled=not question)

if run and question:
    st.divider()

    llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=4000)
    data_summary, _ = get_data_summary()

    def call_agent(system_prompt, user_content):
        messages = [
            SystemMessage(content=system_prompt + "\n\nBe concise: 300-400 words maximum. No filler, no repetition."),
            HumanMessage(content=user_content)
        ]
        return llm.invoke(messages).content

    # ── Run agents one by one, updating UI after each ──────────────────────────
    st.markdown("### Agents at work...")

    p1 = st.empty()
    p2 = st.empty()
    p3 = st.empty()
    p4 = st.empty()
    p5 = st.empty()

    p1.status("🔍 Investigator — thinking...", state="running")
    investigator = call_agent(INVESTIGATOR_PROMPT,
        f"Question: {question}\n\nData Summary:\n{data_summary}")
    p1.status("🔍 Investigator — done", state="complete")

    p2.status("📊 Statistician — thinking...", state="running")
    statistician = call_agent(STATISTICIAN_PROMPT,
        f"Question: {question}\n\nData Summary:\n{data_summary}\n\nInvestigator:\n{investigator}")
    p2.status("📊 Statistician — done", state="complete")

    p3.status("🧠 Causal Analyst — thinking...", state="running")
    causal = call_agent(CAUSAL_ANALYST_PROMPT,
        f"Question: {question}\n\nData Summary:\n{data_summary}\n\nInvestigator:\n{investigator}\n\nStatistician:\n{statistician}")
    p3.status("🧠 Causal Analyst — done", state="complete")

    p4.status("🤨 Skeptic — thinking...", state="running")
    skeptic = call_agent(SKEPTIC_PROMPT,
        f"Question: {question}\n\nData Summary:\n{data_summary}\n\nInvestigator:\n{investigator}\n\nStatistician:\n{statistician}\n\nCausal Analyst:\n{causal}")
    p4.status("🤨 Skeptic — done", state="complete")

    p5.status("📝 Reporter — thinking...", state="running")
    reporter = call_agent(REPORTER_PROMPT,
        f"Original question: {question}\n\nInvestigator:\n{investigator}\n\nStatistician:\n{statistician}\n\nCausal Analyst:\n{causal}\n\nSkeptic:\n{skeptic}\n\nRemember: end with 'The Confession' that directly answers: {question}")
    p5.status("📝 Reporter — done", state="complete")

    # ── Display results ────────────────────────────────────────────────────────
    st.success("Analysis complete!")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Investigator",
        "📊 Statistician",
        "🧠 Causal Analyst",
        "🤨 Skeptic",
        "📝 Final Report"
    ])

    with tab1:
        st.markdown(investigator)
    with tab2:
        st.markdown(statistician)
    with tab3:
        st.markdown(causal)
    with tab4:
        st.markdown(skeptic)
    with tab5:
        st.markdown(reporter)
        st.divider()
        st.download_button(
            label="Download Report",
            data=reporter,
            file_name="data_confessions_report.md",
            mime="text/markdown"
        )