import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.tools import TOOLS
from src.tools.calculator import Calculator, calculator
from src.tools import search_tool
from src.tools.search_tool import browse_url, extract_product_info, search_web


class StubLLM:
    model_name = "stub"

    def generate(self, prompt, system_prompt=None):
        return {"content": "Final Answer: done"}


class ReActStubLLM:
    model_name = "stub-react"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, system_prompt=None):
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return {
                "content": (
                    "Thought: I should inspect the product page.\n"
                    "Action: extract_product_info(https://www.apple.com/shop/buy-iphone)"
                )
            }

        assert "Observation: Title: iPhone 15" in prompt
        return {"content": "Final Answer: iPhone 15 is in stock at $799."}


class MixedActionFinalAnswerStubLLM:
    model_name = "stub-mixed"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, system_prompt=None):
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return {
                "content": (
                    "Thought: I need current stock.\n"
                    "Action: extract_product_info(https://www.apple.com/shop/buy-iphone)\n"
                    "Final Answer: iphone is definitely available."
                )
            }

        assert "Observation: Title: iPhone 15" in prompt
        return {"content": "Final Answer: iPhone 15 is in stock at $799."}


class UnparseableStubLLM:
    model_name = "stub-unparseable"

    def generate(self, prompt, system_prompt=None):
        return {"content": "I cannot follow the required format."}


class ActionOnlyStubLLM:
    model_name = "stub-action-only"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, system_prompt=None):
        self.calls += 1
        return {"content": "Thought: keep trying.\nAction: echo(value)"}


class TavilyClientStub:
    def __init__(self):
        self.search_calls = []
        self.extract_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {
            "results": [
                {
                    "title": "Apple iPhone product page",
                    "url": "https://www.apple.com/shop/buy-iphone",
                    "content": "Current iPhone price and buying information.",
                }
            ]
        }

    def extract(self, **kwargs):
        self.extract_calls.append(kwargs)
        return {
            "results": [
                {
                    "url": "https://www.apple.com/shop/buy-iphone",
                    "raw_content": "iPhone 15\nPrice: $799\nAvailability: In stock\nShips today.",
                }
            ],
            "failed_results": [],
        }


class EmptySearchTavilyClientStub:
    def search(self, **kwargs):
        return {"results": []}


class EmptyExtractTavilyClientStub:
    def extract(self, **kwargs):
        return {"results": []}


class ErrorTavilyClientStub:
    def search(self, **kwargs):
        raise RuntimeError("network unavailable")

    def extract(self, **kwargs):
        raise RuntimeError("network unavailable")


def stub_extract_product_info(url):
    return "Title: iPhone 15\nPrice: $799\nAvailability: In stock\nURL: " + url


REACT_TEST_TOOLS = [
    {
        "name": "extract_product_info",
        "description": "Extract product title, price, and availability from a product URL.",
        "function": stub_extract_product_info,
    }
]

ACTION_ONLY_TEST_TOOLS = [
    {
        "name": "echo",
        "description": "Return the given value.",
        "function": lambda value: value,
    }
]


def test_system_prompt_defines_ecommerce_react_contract():
    agent = ReActAgent(llm=StubLLM(), tools=TOOLS)

    prompt = agent.get_system_prompt()

    assert "ecommerce search agent" in prompt.lower()
    assert "Thought:" in prompt
    assert "Action:" in prompt
    assert "Observation:" in prompt
    assert "Final Answer:" in prompt
    assert "one tool action" in prompt.lower()
    assert "do not invent" in prompt.lower()


def test_system_prompt_lists_available_tools():
    agent = ReActAgent(llm=StubLLM(), tools=TOOLS)

    prompt = agent.get_system_prompt()

    for tool in TOOLS:
        assert tool["name"] in prompt
        assert tool["description"] in prompt


def test_react_loop_executes_tool_and_uses_observation():
    llm = ReActStubLLM()
    agent = ReActAgent(llm=llm, tools=REACT_TEST_TOOLS, max_steps=2)

    answer = agent.run("Is iphone available?")

    assert answer == "iPhone 15 is in stock at $799."
    assert len(llm.prompts) == 2


def test_react_loop_prioritizes_action_before_final_answer():
    llm = MixedActionFinalAnswerStubLLM()
    agent = ReActAgent(llm=llm, tools=REACT_TEST_TOOLS, max_steps=2)

    answer = agent.run("Is iphone available?")

    assert answer == "iPhone 15 is in stock at $799."
    assert len(llm.prompts) == 2


def test_parse_action_stops_at_end_of_action_line():
    agent = ReActAgent(llm=StubLLM(), tools=TOOLS)

    action = agent._parse_action(
        "Thought: Search first.\n"
        "Action: search_web(iphone)\n"
        "Thought: I should not be part of the argument (ignore me)."
    )

    assert action == {"tool_name": "search_web", "args": "iphone"}


def test_run_returns_parse_error_for_unparseable_llm_response():
    agent = ReActAgent(llm=UnparseableStubLLM(), tools=TOOLS)

    assert agent.run("hello") == "Could not parse LLM response."


def test_run_returns_max_steps_when_actions_never_finish():
    llm = ActionOnlyStubLLM()
    agent = ReActAgent(llm=llm, tools=ACTION_ONLY_TEST_TOOLS, max_steps=2)

    assert agent.run("loop") == "Max steps reached without final answer."
    assert llm.calls == 2


def test_execute_tool_reports_unknown_tool():
    agent = ReActAgent(llm=StubLLM(), tools=TOOLS)

    assert agent._execute_tool("missing_tool", "iphone") == "Tool missing_tool not found."


def test_search_tool_uses_tavily_results(monkeypatch):
    client = TavilyClientStub()
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(search_tool, "_create_tavily_client", lambda api_key: client)

    result = search_web("iphone")

    assert "iphone" in result.lower()
    assert "https://www.apple.com/shop/buy-iphone" in result
    assert client.search_calls == [
        {"query": "iphone", "search_depth": "basic", "max_results": 5}
    ]


def test_search_tool_reports_missing_tavily_key(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: None)

    assert search_web("iphone") == "Tavily search error: TAVILY_API_KEY is not set."


def test_search_tool_rejects_empty_query():
    assert search_web("   ") == "Tavily search error: query is empty."


def test_search_tool_reports_empty_tavily_results(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: EmptySearchTavilyClientStub(),
    )

    assert search_web("iphone") == "No Tavily search results found."


def test_search_tool_reports_tavily_exception(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: ErrorTavilyClientStub(),
    )

    assert search_web("iphone") == "Tavily search error: network unavailable"


def test_tool_registry_contains_only_production_ecommerce_tools():
    tool_names = [tool["name"] for tool in TOOLS]
    tool_text = "\n".join(
        f"{tool['name']} {tool['description']}" for tool in TOOLS
    ).lower()

    assert "check_stock" not in tool_names
    assert "get_discount" not in tool_names
    assert "extract_product_info" in tool_names
    assert "winner" not in tool_text
    assert "student" not in tool_text
    assert "demo" not in tool_text


def test_system_prompt_does_not_advertise_hardcoded_coupon_tools():
    agent = ReActAgent(llm=StubLLM(), tools=TOOLS)

    prompt = agent.get_system_prompt().lower()

    assert "winner" not in prompt
    assert "student" not in prompt
    assert "apply coupon discounts" not in prompt


def test_browse_tool_uses_tavily_extract(monkeypatch):
    client = TavilyClientStub()
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(search_tool, "_create_tavily_client", lambda api_key: client)

    result = browse_url("https://www.apple.com/shop/buy-iphone")

    assert "iphone" in result.lower()
    assert "Availability: In stock" in result
    assert client.extract_calls == [
        {"urls": ["https://www.apple.com/shop/buy-iphone"], "include_images": False}
    ]


def test_browse_tool_rejects_empty_url():
    assert browse_url("   ") == "Tavily extract error: URL is empty."


def test_browse_tool_reports_missing_tavily_key(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: None)

    assert (
        browse_url("https://www.apple.com/shop/buy-iphone")
        == "Tavily extract error: TAVILY_API_KEY is not set."
    )


def test_browse_tool_reports_empty_tavily_extract(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: EmptyExtractTavilyClientStub(),
    )

    assert (
        browse_url("https://www.apple.com/shop/buy-iphone")
        == "Tavily extract error: No Tavily page content found for https://www.apple.com/shop/buy-iphone."
    )


def test_browse_tool_reports_tavily_exception(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: ErrorTavilyClientStub(),
    )

    assert (
        browse_url("https://www.apple.com/shop/buy-iphone")
        == "Tavily extract error: network unavailable"
    )


def test_extract_product_info_uses_tavily_and_parses_product_fields(monkeypatch):
    client = TavilyClientStub()
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(search_tool, "_create_tavily_client", lambda api_key: client)

    result = extract_product_info("https://www.apple.com/shop/buy-iphone")

    assert "Title: iPhone 15" in result
    assert "Price: $799" in result
    assert "Availability: In stock" in result
    assert "URL: https://www.apple.com/shop/buy-iphone" in result
    assert client.extract_calls == [
        {"urls": ["https://www.apple.com/shop/buy-iphone"], "include_images": False}
    ]


def test_extract_product_info_rejects_empty_url():
    assert extract_product_info("   ") == "Product extraction error: URL is empty."


def test_extract_product_info_reports_missing_tavily_key(monkeypatch):
    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: None)

    assert (
        extract_product_info("https://www.apple.com/shop/buy-iphone")
        == "Product extraction error: TAVILY_API_KEY is not set."
    )


def test_extract_product_info_reports_unknown_fields(monkeypatch):
    class UnknownFieldsTavilyClientStub:
        def extract(self, **kwargs):
            return {"results": [{"raw_content": "Minimal product page without structured fields."}]}

    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: UnknownFieldsTavilyClientStub(),
    )

    result = extract_product_info("https://www.apple.com/shop/buy-iphone")

    assert "Title: Minimal product page without structured fields." in result
    assert "Price: Unknown" in result
    assert "Availability: Unknown" in result


def test_extract_product_info_trims_long_evidence(monkeypatch):
    class LongContentTavilyClientStub:
        def extract(self, **kwargs):
            return {
                "results": [
                    {
                        "raw_content": (
                            "iPhone 15\nPrice: $799\nAvailability: In stock\n"
                            + ("Long content. " * 200)
                        )
                    }
                ]
            }

    monkeypatch.setattr(search_tool, "_get_tavily_api_key", lambda: "tvly-test")
    monkeypatch.setattr(
        search_tool,
        "_create_tavily_client",
        lambda api_key: LongContentTavilyClientStub(),
    )

    result = extract_product_info("https://www.apple.com/shop/buy-iphone")

    assert result.endswith("...")
    assert len(result) < 1500


def test_calculator_only_allows_simple_arithmetic():
    assert calculator("1000 * 0.9") == "900.0"
    assert calculator("().__class__") == "Calculator error: unsupported expression."


def test_calculator_supports_parentheses_and_unary_operators():
    assert calculator("-(1000 - 200) / 4") == "-200.0"
    assert calculator("+5") == "5"


def test_calculator_reports_syntax_errors():
    assert calculator("1000 *").startswith("Calculator error:")


def test_calculator_class_delegates_to_calculator_function():
    assert Calculator().calculate("2 + 3") == "5"
