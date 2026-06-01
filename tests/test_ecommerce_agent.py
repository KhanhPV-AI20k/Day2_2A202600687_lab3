import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.tools.calculator import calculator
from src.tools.search_tool import browse_url, search_web


class FakeLLM:
    model_name = "fake"

    def generate(self, prompt, system_prompt=None):
        return {"content": "Final Answer: done"}


class ReActFakeLLM:
    model_name = "fake-react"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, system_prompt=None):
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return {"content": "Thought: I should check inventory.\nAction: check_stock(iphone)"}

        assert "Observation: iphone has 5 items in stock." in prompt
        return {"content": "Final Answer: iphone has 5 items in stock."}


class MixedActionFinalAnswerLLM:
    model_name = "fake-mixed"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, system_prompt=None):
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return {
                "content": (
                    "Thought: I need current stock.\n"
                    "Action: check_stock(iphone)\n"
                    "Final Answer: iphone is definitely available."
                )
            }

        assert "Observation: iphone has 5 items in stock." in prompt
        return {"content": "Final Answer: iphone has 5 items in stock."}


def test_system_prompt_defines_ecommerce_react_contract():
    agent = ReActAgent(llm=FakeLLM(), tools=TOOLS)

    prompt = agent.get_system_prompt()

    assert "ecommerce search agent" in prompt.lower()
    assert "Thought:" in prompt
    assert "Action:" in prompt
    assert "Observation:" in prompt
    assert "Final Answer:" in prompt
    assert "one tool action" in prompt.lower()
    assert "do not invent" in prompt.lower()


def test_system_prompt_lists_available_tools():
    agent = ReActAgent(llm=FakeLLM(), tools=TOOLS)

    prompt = agent.get_system_prompt()

    for tool in TOOLS:
        assert tool["name"] in prompt
        assert tool["description"] in prompt


def test_react_loop_executes_tool_and_uses_observation():
    llm = ReActFakeLLM()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=2)

    answer = agent.run("Is iphone available?")

    assert answer == "iphone has 5 items in stock."
    assert len(llm.prompts) == 2


def test_react_loop_prioritizes_action_before_final_answer():
    llm = MixedActionFinalAnswerLLM()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=2)

    answer = agent.run("Is iphone available?")

    assert answer == "iphone has 5 items in stock."
    assert len(llm.prompts) == 2


def test_parse_action_stops_at_end_of_action_line():
    agent = ReActAgent(llm=FakeLLM(), tools=TOOLS)

    action = agent._parse_action(
        "Thought: Search first.\n"
        "Action: search_web(iphone)\n"
        "Thought: I should not be part of the argument (ignore me)."
    )

    assert action == {"tool_name": "search_web", "args": "iphone"}


def test_search_tool_is_ecommerce_focused():
    result = search_web("iphone")

    assert "iphone" in result.lower()
    assert "shop.example.com/iphone" in result
    assert search_web("vinuni") == "No ecommerce search result found in demo data."


def test_browse_tool_is_ecommerce_focused():
    result = browse_url("https://shop.example.com/macbook")

    assert "macbook" in result.lower()
    assert "$2000" in result
    assert browse_url("https://vinuni.edu.vn") == "No ecommerce page found in demo browse data."


def test_calculator_only_allows_simple_arithmetic():
    assert calculator("1000 * 0.9") == "900.0"
    assert calculator("().__class__") == "Calculator error: unsupported expression."
