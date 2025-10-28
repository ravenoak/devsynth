#!/usr/bin/env python3

"""
=== INSTRUCTIONS FOR JUNIE ===

This script enables intelligent web searching using a LangChain-powered agent with dialectical reasoning.
You can send complex or structured questions, and the agent will determine how to search,
retrieve, synthesize, and present the results from the web using the Serper API.

Usage:
    python agentic_serper_search.py "<your complex query>"

Examples:
    python agentic_serper_search.py "Summarize recent developments in LangChain and how it compares to Haystack."
    python agentic_serper_search.py "What are the main limitations of using vector databases in production in 2025?"

The agent will:
1. Analyze your query using dialectical reasoning.
2. Break down complex questions into key components.
3. Search for information on each component using Google Serper.
4. Consider multiple perspectives and potential contradictions.
5. Synthesize a balanced, evidence-based response.
6. Return a structured, human-readable response between:
   ===BEGIN_RESULTS===
   ...
   ===END_RESULTS===

The only thing you need to parse is the content between the markers.
Do not attempt to search or process websites yourself.

Requirements:
- A .env file in the project root with the following variables:
  - SERPER_API_KEY: Your Google Serper API key
  - OPENAI_API_KEY: Your OpenAI API key

=== END INSTRUCTIONS ===
"""

import os
import sys

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools.base import BaseTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI


def run_search_agent(query: str) -> str:
    """
    Execute a web search using dialectical reasoning and return a comprehensive response.

    This function initializes a LangChain agent with a custom prompt template that
    encourages dialectical reasoning. The agent uses Google Serper to search the web
    and synthesizes the results into a comprehensive, balanced response.

    Args:
        query (str): The search query or question to be answered

    Returns:
        str: A comprehensive response synthesized from web search results

    Raises:
        EnvironmentError: If required API keys are missing
        Exception: For other errors during execution
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get environment keys
    serper_api_key = os.getenv("SERPER_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not serper_api_key or not openai_api_key:
        raise OSError("Missing SERPER_API_KEY or OPENAI_API_KEY.")

    # Initialize tools
    search_tool = GoogleSerperAPIWrapper(serper_api_key=serper_api_key)

    # Define the tool in a format compatible with LangGraph
    from langchain.tools.base import BaseTool

    class WebSearchTool(BaseTool):
        name: str = "WebSearch"
        description: str = (
            "Use this to search for real-time information about current events, tools, definitions, or any other factual information from the web. Use this for any questions requiring up-to-date information."
        )

        def _run(self, query: str) -> str:
            return search_tool.run(query)

        async def _arun(self, query: str) -> str:
            # This is a placeholder for async implementation
            return self._run(query)

    tools = [WebSearchTool()]

    # Create a custom prompt template for dialectical reasoning that includes the required variables for ReAct agent
    dialectical_template = """You are an advanced search assistant using dialectical reasoning to provide comprehensive answers.

QUERY: {input}

APPROACH:
1. For ANY query, ALWAYS start by using the WebSearch tool to search for factual information
2. For simple factual queries (e.g., "What is the capital of France?"), directly use the search results
3. For complex queries, break down the query into key components and search for information on each component
4. Analyze multiple perspectives and potential contradictions
5. Synthesize a balanced, evidence-based response
6. Structure your answer clearly with sections and bullet points when appropriate

GUIDELINES:
- ALWAYS use the WebSearch tool first before attempting to answer
- Base your answers on the search results, not on your pre-existing knowledge
- For simple factual queries, provide a direct answer based on the search results
- For complex queries, use multiple searches to gather diverse viewpoints
- Consider opposing arguments and counterpoints
- Cite specific sources when possible
- Acknowledge limitations in available information
- Provide a nuanced, well-reasoned conclusion

TOOLS:
------
You have access to the following tools:

{tools}

To use a tool, please use the following format:
```
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
```
Final Answer: <your response here>
```

Begin your analysis now, using the WebSearch tool to gather information.

{agent_scratchpad}
"""

    # Initialize the LLM and agent
    # llm = ChatOpenAI(temperature=0, api_key=None, model="qwen3-30b-a3b", base_url="http://localhost:1234/v1")

    # gpt-4.1-2025-04-14
    # gpt-4o-mini-2024-07-18
    llm = ChatOpenAI(
        temperature=0, api_key=openai_api_key, model="gpt-4o-mini-2024-07-18"
    )

    # Create the prompt template with all required variables
    prompt = PromptTemplate(
        template=dialectical_template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
    )

    # Create a ReAct agent using LangGraph instead of LangChain's initialize_agent
    # This eliminates the deprecation warning and provides more flexibility

    # Create a ReAct agent using LangChain's create_react_agent
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    # Create the agent executor with the agent and tools
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, max_iterations=10, verbose=True
    )

    # Run the query through the agent
    result = agent_executor.invoke({"input": query})

    # Extract the result from the output
    if isinstance(result, dict) and "output" in result:
        return result["output"]
    else:
        return str(result)


def main():
    """
    Main entry point for the script.

    Parses command-line arguments, executes the search agent, and prints the results.
    The results are enclosed between ===BEGIN_RESULTS=== and ===END_RESULTS=== markers
    to make them easy to parse by other programs.

    Command-line usage:
        python agentic_serper_search.py "<your query>"
    """
    if len(sys.argv) < 2:
        print("Usage: python agentic_serper_search.py '<your query>'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    try:
        result = run_search_agent(query)
        print("===BEGIN_RESULTS===\n" + result.strip() + "\n===END_RESULTS===")
    except OSError as e:
        print(
            f"===BEGIN_RESULTS===\nConfiguration Error: {str(e)}\nPlease ensure you have a .env file in the project root with SERPER_API_KEY and OPENAI_API_KEY variables set.\n===END_RESULTS==="
        )
    except Exception as e:
        print(
            f"===BEGIN_RESULTS===\nError: {str(e)}\nPlease try again with a more specific query or check your internet connection.\n===END_RESULTS==="
        )


if __name__ == "__main__":
    main()
