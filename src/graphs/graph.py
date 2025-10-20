# graph.py
from __future__ import annotations
from typing import TypedDict, Literal, Dict, Any, List, Optional
from dataclasses import dataclass
from time import time
import os

try:
    from langgraph.graph import StateGraph, END
except Exception:
    raise RuntimeError("Please install langgraph: pip install langgraph")

Route = Literal["price", "recommend", "info", "validate", "noop"]

class AgentState(TypedDict, total=False):
    query: str
    route: Route
    context: Dict[str, Any]
    results: Dict[str, Any]
    logs: List[str]
    history: List[Dict[str, Any]]

@dataclass
class VectorDB:
    path: str
    def search(self, text: str, k: int = 10) -> List[Dict[str, Any]]:
        return [{"id": f"item_{i}", "score": 1.0/(i+1), "title": f"Stub {i}", "desc": "stub"} for i in range(k)]

@dataclass
class WebSearch:
    def search(self, q: str, k: int = 5) -> List[Dict[str, Any]]:
        return [{"title": f"result {i}", "url": f"https://example.com/{i}", "snippet": "stub"} for i in range(k)]

@dataclass
class ModelService:
    name: str
    def infer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"output": f"{self.name}::ok", "meta": {"latency_ms": 12}}

def now_ms() -> int:
    return int(time() * 1000)

def _append_log(state: AgentState, msg: str) -> AgentState:
    logs = state.get("logs", [])
    logs.append(msg)
    state["logs"] = logs
    return state

def router(state: AgentState) -> AgentState:
    q = state.get("query", "").lower()
    r: Route = "noop"
    if any(x in q for x in ["가격", "시세", "price"]):
        r = "price"
    elif any(x in q for x in ["추천", "recommend", "유사", "비슷"]):
        r = "recommend"
    elif any(x in q for x in ["정보", "요약", "설명", "qa", "질문"]):
        r = "info"
    elif any(x in q for x in ["검증", "validation", "품질", "정합"]):
        r = "validate"
    state["route"] = r
    _append_log(state, f"route={r}")
    return state

def price_agent(state: AgentState) -> AgentState:
    ws: WebSearch = state["context"]["web"]
    ms: ModelService = state["context"]["model"]
    q = state.get("query", "")
    hits = ws.search(q, k=5)
    pred = ms.infer({"task": "price", "hits": hits, "query": q})
    res = state.get("results", {})
    res["price"] = {"web_hits": hits, "estimate": 123456, "model": pred}
    state["results"] = res
    _append_log(state, "price_agent:ok")
    return state

def recommend_agent(state: AgentState) -> AgentState:
    vdb: VectorDB = state["context"]["vec"]
    ms: ModelService = state["context"]["model"]
    q = state.get("query", "")
    items = vdb.search(q, k=12)
    scores = [{"id": it["id"], "score": it["score"]} for it in items]
    rerank = ms.infer({"task": "rerank", "items": items, "query": q})
    res = state.get("results", {})
    res["recommend"] = {"retrieved": items, "scores": scores, "rerank": rerank}
    state["results"] = res
    _append_log(state, "recommend_agent:ok")
    return state

def info_agent(state: AgentState) -> AgentState:
    vdb: VectorDB = state["context"]["vec"]
    ms: ModelService = state["context"]["model"]
    q = state.get("query", "")
    ctx = vdb.search(q, k=5)
    ans = ms.infer({"task": "qa", "context": ctx, "query": q})
    res = state.get("results", {})
    res["info"] = {"context": ctx, "answer": ans}
    state["results"] = res
    _append_log(state, "info_agent:ok")
    return state

def validate_agent(state: AgentState) -> AgentState:
    vdb: VectorDB = state["context"]["vec"]
    q = state.get("query", "")
    sample = vdb.search(q, k=20)
    ok = all("id" in it for it in sample)
    res = state.get("results", {})
    res["validate"] = {"sample_n": len(sample), "schema_ok": ok}
    state["results"] = res
    _append_log(state, "validate_agent:ok")
    return state

def postprocess(state: AgentState) -> AgentState:
    r = state.get("route", "noop")
    res = state.get("results", {})
    payload: Dict[str, Any]
    if r == "price":
        payload = {"type": "price_estimation", "data": res.get("price", {})}
    elif r == "recommend":
        payload = {"type": "recommendation", "data": res.get("recommend", {})}
    elif r == "info":
        payload = {"type": "info", "data": res.get("info", {})}
    elif r == "validate":
        payload = {"type": "validate", "data": res.get("validate", {})}
    else:
        payload = {"type": "noop", "data": {}}
    res["final"] = payload
    state["results"] = res
    _append_log(state, "postprocess:ok")
    hist = state.get("history", [])
    hist.append({"query": state.get("query", ""), "route": r, "final": payload})
    state["history"] = hist
    return state

def build_graph() -> Any:
    g = StateGraph(AgentState)
    g.add_node("router", router)
    g.add_node("price", price_agent)
    g.add_node("recommend", recommend_agent)
    g.add_node("info", info_agent)
    g.add_node("validate", validate_agent)
    g.add_node("postprocess", postprocess)
    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        lambda s: s.get("route", "noop"),
        {
            "price": "price",
            "recommend": "recommend",
            "info": "info",
            "validate": "validate",
            "noop": "postprocess",
        },
    )
    g.add_edge("price", "postprocess")
    g.add_edge("recommend", "postprocess")
    g.add_edge("info", "postprocess")
    g.add_edge("validate", "postprocess")
    g.add_edge("postprocess", END)
    return g.compile()

def make_context() -> Dict[str, Any]:
    vec_path = os.getenv("VECTOR_DB_PATH", "./vec.index")
    model_name = os.getenv("MODEL_NAME", "stub-model")
    return {
        "vec": VectorDB(vec_path),
        "web": WebSearch(),
        "model": ModelService(model_name),
        "dt": now_ms(),
    }

def run_once(query: str) -> Dict[str, Any]:
    graph = build_graph()
    state: AgentState = {
        "query": query,
        "context": make_context(),
        "results": {},
        "logs": [],
        "history": [],
    }
    out = graph.invoke(state)
    return out  # contains results, logs, history

if __name__ == "__main__":
    q = "아이패드 미니6 중고 가격 시세 알려줘"
    out = run_once(q)
    final = out.get("results", {}).get("final", {})
    import sys, json
    sys.stdout.write(json.dumps(final, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
