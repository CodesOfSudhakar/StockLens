from typing import TypedDict


class PipelineState(TypedDict, total=False):
    """Shared state threaded through the LangGraph pipeline."""

    symbol: str
    # raw inputs collected before the graph runs
    facts: dict
    # each specialist writes its own slot
    technical: dict
    oi: dict
    news: dict
    # supervisor's synthesis
    final: dict
