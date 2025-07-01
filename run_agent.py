import os

from dotenv import load_dotenv

from minimal_agent.agent import Agent
from minimal_agent.tools import VisitWebpageTool, WebSearchTool

_ = load_dotenv(".env", override=True)
tavily_api_key = os.environ.get("TAVILY_API_KEY")


if __name__ == "__main__":
    agent = Agent(
        model=os.environ.get("MODEL"),
        tools=[
            WebSearchTool(max_results=10, tavily_api_key=tavily_api_key),
            VisitWebpageTool(max_output_length=1000),
        ],
    )

    res = agent.run(
        "What was the hottest day in 2024 and how much was the Dow Jones on that day?"
    )

    print(20 * "-")
    print(f"The final answer is:\n\n{res}")
