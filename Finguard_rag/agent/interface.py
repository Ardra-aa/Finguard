"""
AGENT MODULE INTERFACE
Amala P Ansalem — M7

Public function that orchestrates multi-hop compliance reasoning using ReAct loop.
"""
from finguard_rag.schemas.document_schema import (
    UserContext, AgentResponse, ComplianceResponse
)


def agent_run(
    query: str,
    user_context: UserContext,
    mock_mode: bool = False
) -> AgentResponse:
    """
    Run the FinGuard AI Agent to orchestrate multi-hop compliance reasoning.
    
    The agent uses ReAct (Reason + Act) prompting with LangChain AgentExecutor:
      - Tool Registry: retrieve_compliant_docs, check_compliance_rules, 
                       detect_jurisdiction_conflict, scan_leakage_risk,
                       explain_regulation, get_document_history
      - Reasoning Loop: agent decides which tool to call and in what order
      - Hard Limit: max_iterations = 10 (configurable in config.yaml)
    
    For simple queries: agent routes directly to retrieve() + generate()
    For complex multi-hop queries: agent chains multiple tool calls
    
    Args:
        query: User's compliance question
        user_context: UserContext with role, jurisdiction, session_id
        mock_mode: If True, return dummy AgentResponse instantly
    
    Returns:
        AgentResponse: final_response (ComplianceResponse) + agent_trace (THINK/ACT/OBS steps)
    
    Raises:
        Exception: If agent exceeds max_iterations or tool call fails
    
    Example:
        >>> ctx = UserContext(..., role='compliance_officer', ...)
        >>> agent_response = agent_run(
        ...     'What are insider trading disclosure rules under SEBI vs Companies Act?',
        ...     ctx
        ... )
        >>> print(agent_response.final_response.answer)
        >>> for step in agent_response.agent_trace:
        ...     print(f"[{step['type']}] {step['content']}")
    """
    if mock_mode:
        # Return dummy AgentResponse with sample trace for testing/development
        dummy_trace = [
            {'type': 'THINK', 'content': 'This is a multi-hop query comparing SEBI and Companies Act rules.'},
            {'type': 'ACT', 'content': 'retrieve_compliant_docs("SEBI insider trading disclosure", jurisdiction="IN")'},
            {'type': 'OBS', 'content': '3 chunks retrieved: SEBI PIT Regulations, SEBI LODR Reg 7, SEBI LODR Schedule III'},
            {'type': 'ACT', 'content': 'retrieve_compliant_docs("Companies Act Section 195 insider trading")'},
            {'type': 'OBS', 'content': '2 chunks retrieved: Section 195, Insider Trading Rules'},
            {'type': 'ACT', 'content': 'detect_jurisdiction_conflict(docs=[SEBI_results, CompaniesAct_results])'},
            {'type': 'OBS', 'content': 'Minor conflict: SEBI T+2 vs Companies Act no explicit timeline'},
            {'type': 'THINK', 'content': 'Both applicable. SEBI LODR T+2 is the binding operative rule.'},
        ]
        
        dummy_final_response = ComplianceResponse(
            answer="""Insider trading disclosure requirements are governed by both SEBI LODR 2015 
            and Companies Act 2013. SEBI Regulation 7 requires disclosure within 2 trading days. 
            The Companies Act Section 195 imposes stricter penalties but does not specify timeline.
            Conservative approach: follow SEBI T+2 deadline as the operative rule.""",
            sources=[],
            compliance_status='PASS',
            violations=[],
            conflicts=['SEBI_LODR_T+2 vs Companies_Act_Section_195'],
            leakage_risk='NONE',
            confidence_score=0.88,
            agent_trace=None
        )
        
        return AgentResponse(
            final_response=dummy_final_response,
            agent_trace=dummy_trace,
            total_iterations=4
        )
    
    # TODO: Implement actual agent pipeline
    # M7: ReAct Agent with LangChain AgentExecutor
    #     - Tool registry wrapping all pipeline functions
    #     - ReAct prompting for reasoning
    #     - Agent trace logging (type: THINK | ACT | OBS)
    #     - Hard limit on iterations
    raise NotImplementedError('Agent pipeline not yet implemented by Amala')
