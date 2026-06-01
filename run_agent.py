import os

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider
from src.tools import TOOLS


def main():
    load_dotenv()

    llm = OpenAIProvider(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=5)

    question = "I want to buy an iphone using coupon WINNER. Check stock and tell me the discount."
    answer = agent.run(question)

    print(answer)


if __name__ == "__main__":
    main()
