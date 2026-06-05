# src/graph.py
"""
LangGraph multi-agent orchestration for data-confessions.
Defines the agent graph: Investigator → Statistician → Causal Analyst → Skeptic → Reporter
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
from dotenv import load_dotenv

from src.tools.data_loader import load_merged_data
from src.prompts import (
    INVESTIGATOR_PROMPT,
    STATISTICIAN_PROMPT,
    CAUSAL_ANALYST_PROMPT,
    SKEPTIC_PROMPT,
    REPORTER_PROMPT,
)

load_dotenv()

# ── State ──────────────────────────────────────────────────────────────────────

class AnalysisState(TypedDict):
    """Shared state passed between agents."""
    question: str           # original user question
    data_summary: str       # loaded once, passed to all agents
    investigator: str       # output of Investigator agent
    statistician: str       # output of Statistician agent
    causal_analyst: str     # output of Causal Analyst agent
    skeptic: str            # output of Skeptic agent
    reporter: str           # final report


# ── LLM ───────────────────────────────────────────────────────────────────────

llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=4000)


# ── Data summary (loaded once) ─────────────────────────────────────────────────

def get_data_summary() -> str:
    """Load data and compute summary statistics to pass to all agents."""
    df = load_merged_data()

    rainy = df[df["precipitation_mm"] > 0]
    dry = df[df["precipitation_mm"] == 0]

    summary = f"""
DATASET: Chicago Crime + Weather (2018-2023)
- Total days: {len(df)}
- Date range: {df['date_only'].min()} to {df['date_only'].max()}
- Total crimes recorded: {df['crime_count'].sum():,}
- Average daily crimes: {df['crime_count'].mean():.1f}
- Rainy days (precipitation > 0mm): {len(rainy)} ({100*len(rainy)/len(df):.1f}%)
- Dry days: {len(dry)} ({100*len(dry)/len(df):.1f}%)

CRIME ON RAINY VS DRY DAYS:
- Avg crimes on rainy days: {rainy['crime_count'].mean():.1f}
- Avg crimes on dry days: {dry['crime_count'].mean():.1f}
- Difference: {dry['crime_count'].mean() - rainy['crime_count'].mean():.1f} fewer crimes on rainy days

WEATHER STATS:
- Avg precipitation (rainy days only): {rainy['precipitation_mm'].mean():.1f}mm
- Max precipitation: {df['precipitation_mm'].max():.1f}mm
- Avg max temperature: {df['temp_max_c'].mean():.1f}°C
- Temperature range: {df['temp_max_c'].min():.1f}°C to {df['temp_max_c'].max():.1f}°C

CORRELATION:
- Pearson correlation (precipitation vs crime): {df['precipitation_mm'].corr(df['crime_count']):.3f}
- Pearson correlation (temperature vs crime): {df['temp_max_c'].corr(df['crime_count']):.3f}
"""
    return summary, df


# ── Agent nodes ────────────────────────────────────────────────────────────────

def run_investigator(state: AnalysisState) -> AnalysisState:
    """Investigator agent: explore and describe the data."""
    print("🔍 Investigator thinking...")
    messages = [
        SystemMessage(content=INVESTIGATOR_PROMPT),
        HumanMessage(content=f"""
Question to investigate: {state['question']}

Data Summary:
{state['data_summary']}

Please provide your investigation findings.
""")
    ]
    response = llm.invoke(messages)
    return {**state, "investigator": response.content}


def run_statistician(state: AnalysisState) -> AnalysisState:
    """Statistician agent: run statistical analysis."""
    print("📊 Statistician thinking...")
    messages = [
        SystemMessage(content=STATISTICIAN_PROMPT),
        HumanMessage(content=f"""
Question: {state['question']}

Data Summary:
{state['data_summary']}

Investigator findings:
{state['investigator']}

Please provide your statistical analysis.
""")
    ]
    response = llm.invoke(messages)
    return {**state, "statistician": response.content}


def run_causal_analyst(state: AnalysisState) -> AnalysisState:
    """Causal Analyst agent: evaluate causal claims."""
    print("🧠 Causal Analyst thinking...")
    messages = [
        SystemMessage(content=CAUSAL_ANALYST_PROMPT),
        HumanMessage(content=f"""
Question: {state['question']}

Data Summary:
{state['data_summary']}

Investigator findings:
{state['investigator']}

Statistician findings:
{state['statistician']}

Please provide your causal analysis.
""")
    ]
    response = llm.invoke(messages)
    return {**state, "causal_analyst": response.content}


def run_skeptic(state: AnalysisState) -> AnalysisState:
    """Skeptic agent: challenge the conclusions."""
    print("🤨 Skeptic thinking...")
    messages = [
        SystemMessage(content=SKEPTIC_PROMPT),
        HumanMessage(content=f"""
Question: {state['question']}

Data Summary:
{state['data_summary']}

Investigator findings:
{state['investigator']}

Statistician findings:
{state['statistician']}

Causal Analyst findings:
{state['causal_analyst']}

Please challenge these findings rigorously.
""")
    ]
    response = llm.invoke(messages)
    return {**state, "skeptic": response.content}


def run_reporter(state: AnalysisState) -> AnalysisState:
    """Reporter agent: synthesize into final report."""
    print("📝 Reporter thinking...")
    messages = [
        SystemMessage(content=REPORTER_PROMPT),
        HumanMessage(content=f"""
Question: {state['question']}

Investigator findings:
{state['investigator']}

Statistician findings:
{state['statistician']}

Causal Analyst findings:
{state['causal_analyst']}

Skeptic findings:
{state['skeptic']}

Please write the final report.
""")
    ]
    response = llm.invoke(messages)
    return {**state, "reporter": response.content}


# ── Graph ──────────────────────────────────────────────────────────────────────

def build_graph():
    """Build and compile the LangGraph agent graph."""
    graph = StateGraph(AnalysisState)

    graph.add_node("investigator", run_investigator)
    graph.add_node("statistician", run_statistician)
    graph.add_node("causal_analyst", run_causal_analyst)
    graph.add_node("skeptic", run_skeptic)
    graph.add_node("reporter", run_reporter)

    graph.set_entry_point("investigator")
    graph.add_edge("investigator", "statistician")
    graph.add_edge("statistician", "causal_analyst")
    graph.add_edge("causal_analyst", "skeptic")
    graph.add_edge("skeptic", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


# ── Run ────────────────────────────────────────────────────────────────────────

def run_analysis(question: str) -> AnalysisState:
    """Run the full multi-agent analysis pipeline."""
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    data_summary, _ = get_data_summary()
    graph = build_graph()

    initial_state = AnalysisState(
        question=question,
        data_summary=data_summary,
        investigator="",
        statistician="",
        causal_analyst="",
        skeptic="",
        reporter="",
    )

    result = graph.invoke(initial_state)
    return result

if __name__ == "__main__":
    result = run_analysis("Does rain reduce crime in Chicago?")
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(result["reporter"])

