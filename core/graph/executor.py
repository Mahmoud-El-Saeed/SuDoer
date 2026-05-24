from __future__ import annotations

from collections.abc import Awaitable, Callable

from langgraph.graph import StateGraph

from core.configs.settings import Settings
from core.graph.state import ExecutorState
from core.security.validator import validate_command


async def _format_command(state: ExecutorState) -> ExecutorState:
    """Summarize formatting the next command from the plan."""

    if state["current_step"] >= len(state["plan"]):
        state["done"] = True
        return state
    state["command"] = state["plan"][state["current_step"]]
    return state


async def _validate_command(state: ExecutorState, settings: Settings) -> ExecutorState:
    """Summarize security validation for the next command."""

    result = validate_command(state["goal"], state["command"], settings)
    state["requires_hitl"] = not result.is_safe
    state["validation_reason"] = result.reason
    return state


async def _observe_exit(state: ExecutorState, exit_code: int) -> ExecutorState:
    """Summarize observer step update."""

    state["last_exit_code"] = exit_code
    if exit_code == 0:
        state["retry_count"] = 0
        state["current_step"] += 1
    else:
        state["retry_count"] += 1
    return state


def build_executor_graph(
    settings: Settings,
    runner: Callable[[str, Callable[[str], Awaitable[None]]], Awaitable[int]],
    request_approval: Callable[[str], Awaitable[bool]],
    on_output: Callable[[str], Awaitable[None]],
) -> StateGraph:
    """Summarize executor LangGraph assembly."""

    graph = StateGraph(ExecutorState)

    async def _run_execute(state: ExecutorState) -> ExecutorState:
        """Summarize executing the command via PTY."""

        async def _on_chunk(chunk: str) -> None:
            await on_output(chunk)

        exit_code = await runner(state["command"], _on_chunk)
        return await _observe_exit(state, exit_code)

    async def _handle_hitl(state: ExecutorState) -> ExecutorState:
        """Summarize approval request and decision."""

        reason = state.get("validation_reason") or "Approval required"
        approved = await request_approval(reason)
        state["approved"] = approved
        if not approved:
            state["done"] = True
        return state

    async def _run_validate(state: ExecutorState) -> ExecutorState:
        """Summarize running validator with settings."""

        return await _validate_command(state, settings)

    graph.add_node("format", _format_command)
    graph.add_node("validate", _run_validate)
    graph.add_node("hitl", _handle_hitl)
    graph.add_node("execute", _run_execute)

    def _needs_validation(state: ExecutorState) -> str:
        if state.get("done"):
            return "finish"
        return "validate"

    def _route_after_validate(state: ExecutorState) -> str:
        if state["requires_hitl"]:
            return "hitl"
        return "execute"

    def _route_after_execute(state: ExecutorState) -> str:
        if state["retry_count"] >= 3:
            state["done"] = True
            return "finish"
        return "format"

    graph.set_entry_point("format")
    graph.add_conditional_edges("format", _needs_validation, {"validate": "validate", "finish": "finish"})
    graph.add_conditional_edges("validate", _route_after_validate, {"hitl": "hitl", "execute": "execute"})

    def _route_after_hitl(state: ExecutorState) -> str:
        if state.get("approved"):
            return "execute"
        return "finish"

    graph.add_conditional_edges("hitl", _route_after_hitl, {"execute": "execute", "finish": "finish"})
    graph.add_conditional_edges("execute", _route_after_execute, {"format": "format", "finish": "finish"})
    graph.add_node("finish", lambda state: state)
    graph.set_finish_point("finish")

    return graph
