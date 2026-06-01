# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Văn Khánh
- **Student ID**: 2A202600687
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

My main contribution was turning the lab skeleton into an ecommerce-focused ReAct agent that can actually use live web tools instead of fake demo data.

- **Modules Implemented**: `src/agent/agent.py`, `src/tools/search_tool.py`, `src/tools/__init__.py`, `src/tools/calculator.py`
- **Code Highlights**:
  - [src/agent/agent.py](/Users/blackpham/Documents/hocaivinuni/2A202600687_lab3/src/agent/agent.py:27) now has an ecommerce-specific system prompt and a ReAct loop that prioritizes `Action` parsing before `Final Answer`.
  - [src/tools/search_tool.py](/Users/blackpham/Documents/hocaivinuni/2A202600687_lab3/src/tools/search_tool.py:12) integrates Tavily through `TAVILY_API_KEY` and supports `search_web`, `browse_url`, and `extract_product_info`.
  - [src/tools/calculator.py](/Users/blackpham/Documents/hocaivinuni/2A202600687_lab3/src/tools/calculator.py:15) was hardened to use AST parsing instead of `eval`.
  - [src/tools/__init__.py](/Users/blackpham/Documents/hocaivinuni/2A202600687_lab3/src/tools/__init__.py:5) now exposes only production-oriented ecommerce tools.
- **Documentation**: The ReAct agent receives tool descriptions from `TOOLS`, then reasons in a `Thought -> Action -> Observation -> Final Answer` loop. Search results and product extraction observations are fed back into the next prompt so the model can ground its next step in live data.

---

## II. Debugging Case Study (10 Points)

One important failure happened in the ReAct loop: the model could emit both `Action:` and `Final Answer:` in the same response, and the agent would return too early instead of using a tool first.

- **Problem Description**: The agent sometimes answered with a final response before executing the requested tool, which made it look correct while actually skipping the observation step.
- **Log Source**: [logs/2026-06-01.log](/Users/blackpham/Documents/hocaivinuni/2A202600687_lab3/logs/2026-06-01.log)
- **Diagnosis**: The issue came from the parsing order in `src/agent/agent.py`. The agent initially treated `Final Answer` as the highest priority, so mixed outputs were accepted too early. The log pattern showed very short agent runs ending after one step, which matched the parsing bug.
- **Solution**: I added regression tests for mixed `Action + Final Answer` outputs and changed the runtime to prioritize `Action` first. I also tightened the action parser so it only accepts a single action line instead of greedily swallowing extra text.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: The `Thought` block helps the agent separate planning from execution. Compared with a direct chatbot answer, ReAct makes the model explain what it needs next before calling a tool, which is much better for live ecommerce tasks like search and product inspection.
2. **Reliability**: The agent can perform worse than a chatbot when the tool set is incomplete or when the model produces malformed `Action` text. In those cases, a direct answer may be faster, but it is less grounded.
3. **Observation**: The observation step is the key feedback loop. For example, `search_web` and `extract_product_info` return live Tavily results, and the next step can use those facts instead of guessing. That makes the agent less imaginative and more trustworthy.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Add a richer tool routing layer so the agent can choose among many ecommerce tools without putting all tool descriptions into one prompt.
- **Safety**: Add structured output validation for tool calls and final answers, plus a supervisor layer for risky actions.
- **Performance**: Cache repeated Tavily queries and product page extractions so the agent does not re-fetch the same pages on every turn.

---

> [!NOTE]
> This report is based on the final code in the repository and the logs generated during development.
