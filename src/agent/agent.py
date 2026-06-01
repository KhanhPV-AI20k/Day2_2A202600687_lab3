import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Build the system prompt that instructs the agent to follow ReAct.
        Includes:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are an ecommerce search agent that follows the ReAct loop.
Help users find products, check prices, verify stock, inspect product pages,
extract product details from URLs, and calculate simple totals using only the
tools below.

Available tools:
{tool_descriptions}

Use this exact format:
Thought: explain the next useful ecommerce search step
Action: tool_name(argument)
Observation: tool result provided by the runtime
Thought: explain what the observation means
Final Answer: concise answer for the user

Rules:
- Use one tool action at a time, then wait for the Observation.
- Use Action only when a tool is needed.
- Use only the tools listed above.
- Do not invent tool results, prices, stock, URLs, or discounts.
- For price or availability, search for a product URL first, then extract product info from that URL.
- For coupons or discounts, search the live web and cite tool observations instead of assuming a code works.
- If a requested product or page is not found, say that clearly.
- When you know the answer, respond with Final Answer.
""".strip()

    def run(self, user_input: str) -> str:
        """
        Run the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        current_prompt = user_input
        steps = 0

        while steps < self.max_steps:
            steps += 1
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())

            response_text = result["content"].strip()

            action = self._parse_action(response_text)
            if action is not None:
                tool_name = action["tool_name"]
                args = action["args"]
                observation = self._execute_tool(tool_name, args)
                current_prompt = (
                    f"{current_prompt}\n\n"
                    f"{response_text}\n"
                    f"Observation: {observation}"
                )
                continue

            final_answer = self._parse_final_answer(response_text)
            if final_answer is not None:
                logger.log_event("AGENT_END", {"steps": steps})
                return final_answer

            logger.log_event("AGENT_END", {"steps": steps})
            return "Could not parse LLM response."

        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without final answer."

    # Function to parse Final Answer from LLM response

    def _parse_final_answer(self, text: str) -> Optional[str]:
        """
        Helper method to extract Final Answer from LLM response.
        """
        match = re.search(r"Final Answer\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        if match is None:
            return None
        return match.group(1).strip()

    # Function to parse Action from LLM response
    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        match = re.search(
            r"^\s*Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*$",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if match is None:
            return None
        return {
            "tool_name": match.group(1).strip(),
            "args": match.group(2).strip()
        }

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                return str(tool["function"](args))
        return f"Tool {tool_name} not found."
