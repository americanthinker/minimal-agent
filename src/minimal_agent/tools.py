from duckduckgo_search.exceptions import DuckDuckGoSearchException


class FinalAnswerTool:
    name = "final_answer"
    description = "Provides a final answer to the given problem."
    inputs = {
        "answer": {"type": "any", "description": "The final answer to the problem"}
    }
    output_type = "any"

    def __call__(self, answer):
        return answer


class VisitWebpageTool:
    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    inputs = {
        "url": {
            "type": "string",
            "description": "The url of the webpage to visit.",
        }
    }
    output_type = "string"

    def __init__(self, max_output_length: int = 40000):
        super().__init__()
        self.max_output_length = max_output_length

    def __call__(self, url: str) -> str:
        try:
            import re

            import requests
            from markdownify import markdownify
            from requests.exceptions import RequestException
            from smolagents.utils import truncate_content
        except ImportError as e:
            raise ImportError(
                "You must install packages `markdownify` and `requests` to run this tool: for instance run `pip install markdownify requests`."
            ) from e
        try:
            # Send a GET request to the URL with a 20-second timeout
            response = requests.get(url, timeout=20)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Convert the HTML content to Markdown
            markdown_content = markdownify(response.text).strip()

            # Remove multiple line breaks
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            return truncate_content(markdown_content, self.max_output_length)

        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


class DuckDuckGoSearchTool:
    name = "web_search"
    description = """Performs a duckduckgo web search based on your query (think a Google search) then returns the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"

    def __init__(self, max_results: int = 10, **kwargs):
        super().__init__()
        self.max_results = max_results
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError(
                "You must install package `duckduckgo_search` to run this tool: for instance run `pip install duckduckgo-search`."
            ) from e
        self.ddgs = DDGS(**kwargs)

    def __call__(self, query: str) -> str:
        results = self.ddgs.text(query, max_results=self.max_results)
        if len(results) == 0:
            raise Exception("No results found! Try a less restrictive/shorter query.")
        postprocessed_results = [
            f"[{result['title']}]({result['href']})\n{result['body']}"
            for result in results
        ]
        return "## Search Results\n\n" + "\n\n".join(postprocessed_results)


class TavilySearchTool:
    name = "web_search"
    description = """Performs a Tavily web search based on your query (think a Google search) then returns the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"

    def __init__(
        self,
        tavily_api_key: str,
        max_results: int = 10,
    ) -> None:
        self.max_results = max_results
        try:
            from tavily import TavilyClient
        except ImportError as e:
            raise ImportError(
                "You must install package `tavily-python` to run this tool: for instance run `uv add tavily-python`."
            ) from e
        self.client = TavilyClient(tavily_api_key)

    def __call__(self, query: str) -> str:
        results = self.client.search(query, include_raw_content="text")  # type: ignore
        if len(results) == 0:
            raise Exception("No results found! Try a less restrictive/shorter query.")
        results = results["results"][: self.max_results]
        postprocessed_results = [
            f"[{result['title']}]({result['content']}" for result in results
        ]
        return "## Search Results\n\n" + "\n\n".join(postprocessed_results)


class WebSearchTool:
    name = "web_search"
    description = """Performs a web search based on your query (think a Google search) then returns the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"

    def __init__(
        self, max_results: int = 10, tavily_api_key: str | None = None
    ) -> None:
        self.ddg = DuckDuckGoSearchTool(max_results=max_results)
        if isinstance(tavily_api_key, str):
            self.tavily = TavilySearchTool(
                max_results=max_results, tavily_api_key=tavily_api_key
            )

    def __call__(self, query: str) -> None:
        try:
            return self.ddg(query)
        except DuckDuckGoSearchException as e:
            print(f"Error using DuckDuckGo search: {e}. Trying Tavily search...")
            return self.tavily(query)
