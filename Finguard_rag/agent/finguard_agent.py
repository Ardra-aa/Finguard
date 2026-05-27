"""
Finguard_rag/agent/finguard_agent.py
Amala P Ansalem — M7: FinGuard AI Agent (ReAct)

LangChain AgentExecutor using ReAct-style reasoning for multi-hop
compliance queries.

Features:
    - Uses Gemini 1.5 Flash as the LLM backbone
    - 6 tools from tool_registry.py
    - max_iterations=10 (from config.yaml)
    - Logs every tool call to an agent_trace list (THINK/ACT/OBS)
    - Returns AgentResponse with the final ComplianceResponse + trace

For simple queries, the agent makes 1–2 tool calls.
For complex multi-hop queries (e.g., "compare SEBI vs Companies Act"),
the agent chains multiple retrieval and validation calls.
"""

import os
import sys
import logging
from datetime import date
from typing import List, Dict, Optional
from pathlib import Path

import yaml
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

load_dotenv(dotenv_path=_REPO_ROOT / ".env")

from Finguard_rag.schemas.document_schema import (
    UserContext,
    AgentResponse,
    ComplianceResponse,
)
from Finguard_rag.agent.tool_registry import build_tools
from Finguard_rag.agent.agent_prompt import get_system_prompt, get_human_message

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


def _load_agent_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("agent", {})
    return {"max_iterations": 10, "timeout_seconds": 60, "log_traces": True}


_AGENT_CFG = _load_agent_config()
MAX_ITERATIONS = _AGENT_CFG.get("max_iterations", 10)


# ---------------------------------------------------------------------------
# Trace-capturing callback handler
# ---------------------------------------------------------------------------
class _TraceCallbackHandler:
    """
    Lightweight callback handler that captures agent reasoning steps
    as a list of {type, content} dicts matching the AgentResponse.agent_trace
    schema.

    This is NOT a LangChain BaseCallbackHandler — it's a simpler wrapper
    that parses the AgentExecutor output dict.
    """

    def __init__(self):
        self.trace: List[Dict[str, str]] = []

    def add(self, step_type: str, content: str):
        self.trace.append({"type": step_type, "content": content})

    def get_trace(self) -> List[Dict[str, str]]:
        return self.trace.copy()


# ---------------------------------------------------------------------------
# Agent builder — creates a LangChain AgentExecutor
# ---------------------------------------------------------------------------
def _build_agent_executor(
    user_context: UserContext,
    mock_mode: bool = False,
):
    """
    Build a LangChain AgentExecutor with the FinGuard tool set.

    Uses ChatGoogleGenerativeAI (Gemini 1.5 Flash) as the LLM.
    Falls back to a simple chain if LangChain agent setup fails.
    """
    import google.generativeai as genai
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com"
        )

    # Build the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.3,
        max_output_tokens=2048,
    )

    # Build tools
    tools = build_tools(user_context, mock_mode=mock_mode)

    # Build the ReAct prompt
    # LangChain's create_react_agent expects a prompt with specific
    # input variables: tools, tool_names, agent_scratchpad, input
    react_template = (
        get_system_prompt(MAX_ITERATIONS) + "\n\n"
        "You have access to the following tools:\n\n"
        "{tools}\n\n"
        "Use the following format:\n\n"
        "Question: the input question you must answer\n"
        "Thought: you should always think about what to do\n"
        "Action: the action to take, should be one of [{tool_names}]\n"
        "Action Input: the input to the action\n"
        "Observation: the result of the action\n"
        "... (this Thought/Action/Action Input/Observation can repeat "
        "N times)\n"
        "Thought: I now know the final answer\n"
        "Final Answer: the final answer to the original input question\n\n"
        "Begin!\n\n"
        "Question: {input}\n"
        "Thought: {agent_scratchpad}"
    )

    prompt = PromptTemplate.from_template(react_template)

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=MAX_ITERATIONS,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    return executor


# ---------------------------------------------------------------------------
# Parse AgentExecutor output into our trace format
# ---------------------------------------------------------------------------
def _parse_agent_output(
    result: dict,
    trace_handler: _TraceCallbackHandler,
) -> tuple:
    """
    Parse AgentExecutor result dict into (answer_text, trace).

    Extracts intermediate_steps and converts them to THINK/ACT/OBS
    entries in the trace.
    """
    # Extract the final answer
    answer_text = result.get("output", "Agent did not produce a final answer.")

    # Extract intermediate steps: list of (AgentAction, observation) tuples
    intermediate_steps = result.get("intermediate_steps", [])

    for step in intermediate_steps:
        if len(step) >= 2:
            action, observation = step[0], step[1]

            # Log the tool call
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", "")
            thought = getattr(action, "log", "")

            # Extract THINK from the agent's log (text before "Action:")
            if thought:
                # The log contains the agent's reasoning
                think_text = thought.split("Action:")[0].strip()
                if think_text:
                    trace_handler.add("THINK", think_text)

            # Log ACT
            trace_handler.add(
                "ACT",
                f"{tool_name}({json.dumps(tool_input) if isinstance(tool_input, dict) else repr(tool_input)})"
            )

            # Log OBS (truncate long observations)
            obs_text = str(observation)[:500]
            trace_handler.add("OBS", obs_text)

    return answer_text, trace_handler.get_trace()


# ---------------------------------------------------------------------------
# Simple fallback agent (no LangChain dependency issues)
# ---------------------------------------------------------------------------
def _run_simple_agent(
    query: str,
    user_context: UserContext,
    mock_mode: bool = False,
) -> AgentResponse:
    """
    Fallback agent that runs a simple retrieve → generate pipeline
    without the full LangChain AgentExecutor.

    Used when LangChain agent setup fails (e.g., missing dependencies).
    """
    trace = _TraceCallbackHandler()

    # Step 1: Retrieve
    trace.add("THINK", f"Processing query: {query}")
    trace.add("ACT", f"retrieve_compliant_docs({repr(query[:60])})")

    from Finguard_rag.retrieval.interface import retrieve
    docs = retrieve(
        query=query,
        user_context=user_context,
        top_k=5,
        mock_mode=mock_mode,
    )
    trace.add(
        "OBS",
        f"{len(docs)} documents retrieved"
        + (f": {', '.join(d.document.doc_id for d in docs[:3])}" if docs else "")
    )

    # Step 2: Check compliance rules on the query itself
    trace.add("ACT", f"check_compliance_rules({repr(query[:60])})")
    if not mock_mode:
        from Finguard_rag.generation.rule_engine import evaluate_rules
        rule_status, rule_violations = evaluate_rules(query)
        trace.add("OBS", f"Rule check: {rule_status}, violations: {rule_violations}")
    else:
        trace.add("OBS", "Rule check: PASS (mock mode)")

    # Step 3: Generate answer
    trace.add("THINK", "Generating compliance-verified answer from retrieved documents.")
    trace.add("ACT", "generate(query, docs, user_context)")

    from Finguard_rag.generation.interface import generate
    response = generate(
        query=query,
        docs=docs,
        user_context=user_context,
        mock_mode=mock_mode,
    )
    trace.add("OBS", f"Answer generated. Status: {response.compliance_status}")

    # Step 4: Leakage scan
    trace.add("ACT", f"scan_leakage_risk({repr(query[:60])})")
    try:
        from Finguard_rag.defense.interface import defend
        defense_result = defend(
            session_id=user_context.session_id,
            user_id=user_context.user_id,
            role=user_context.role,
            query=query,
            response=response.answer,
            source_docs=docs,
            user_context=user_context,
            mock_mode=mock_mode,
        )
        trace.add(
            "OBS",
            f"Leakage: {defense_result['leakage_risk']}, "
            f"Conflicts: {defense_result['conflict_detected']}"
        )

        # Enrich the ComplianceResponse with defense results
        response = ComplianceResponse(
            answer=response.answer,
            sources=response.sources,
            compliance_status=response.compliance_status,
            violations=response.violations,
            conflicts=defense_result.get("conflicting_rules", []),
            leakage_risk=defense_result.get("leakage_risk", "NONE"),
            confidence_score=response.confidence_score,
            agent_trace=trace.get_trace(),
        )
    except Exception as e:
        trace.add("OBS", f"Defense module error: {e}")
        logger.warning("Defense module error in simple agent: %s", e)

    return AgentResponse(
        final_response=response,
        agent_trace=trace.get_trace(),
        total_iterations=len(trace.get_trace()),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
import json


def run_agent(
    query: str,
    user_context: UserContext,
    mock_mode: bool = False,
) -> AgentResponse:
    """
    Run the FinGuard AI Agent.

    Attempts to use the full LangChain AgentExecutor with ReAct.
    Falls back to the simple pipeline agent if LangChain setup fails.

    Args:
        query:        The user's compliance question.
        user_context: Current user metadata (role, jurisdiction, etc.).
        mock_mode:    If True, all tools return mock responses.

    Returns:
        AgentResponse with final_response, agent_trace, and total_iterations.
    """
    # ------------------------------------------------------------------ #
    # Mock mode — instant return
    # ------------------------------------------------------------------ #
    if mock_mode:
        return _run_simple_agent(query, user_context, mock_mode=True)

    # ------------------------------------------------------------------ #
    # Try full LangChain ReAct agent
    # ------------------------------------------------------------------ #
    try:
        logger.info("Starting LangChain ReAct agent for query: %s", query[:80])

        executor = _build_agent_executor(user_context, mock_mode=False)
        trace_handler = _TraceCallbackHandler()

        # Format the input with user context
        human_msg = get_human_message(
            query=query,
            role=user_context.role,
            jurisdiction=user_context.jurisdiction,
            session_id=user_context.session_id,
            reference_date=str(user_context.reference_date),
        )

        result = executor.invoke({"input": human_msg})

        answer_text, trace = _parse_agent_output(result, trace_handler)

        # Build ComplianceResponse from agent output
        final_response = ComplianceResponse(
            answer=answer_text,
            sources=[],  # populated from tool calls if needed
            compliance_status="PASS",
            violations=[],
            conflicts=[],
            leakage_risk="NONE",
            confidence_score=0.85,
            agent_trace=trace,
        )

        return AgentResponse(
            final_response=final_response,
            agent_trace=trace,
            total_iterations=len(trace),
        )

    except Exception as e:
        logger.warning(
            "LangChain AgentExecutor failed (%s) — falling back to simple agent",
            e,
        )
        return _run_simple_agent(query, user_context, mock_mode=False)
