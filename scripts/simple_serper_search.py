#!/usr/bin/env python3

"""
Simple Serper search script for direct web searching.

This script provides a straightforward way to search the web using the Serper API,
without dependencies on LangChain or other complex libraries.

Usage:
    python simple_serper_search.py "<your search query>"

Requirements:
    - SERPER_API_KEY environment variable or .env file
"""

import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv


def setup():
    """Set up the environment and ensure API keys are available."""
    # Load environment variables from .env file
    load_dotenv(override=True)

    # Check for Serper API key
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("Error: SERPER_API_KEY environment variable not found.")
        print("Please set this environment variable or add it to a .env file.")
        sys.exit(1)

    return api_key


def search_serper(query, api_key):
    """
    Execute a search using the Serper API.

    Args:
        query: The search query
        api_key: The Serper API key

    Returns:
        The search results
    """
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    payload = {"q": query, "gl": "us", "hl": "en"}

    try:
        response = requests.post(
            "https://google.serper.dev/search", headers=headers, json=payload
        )

        # Check if the request was successful
        response.raise_for_status()

        # Parse the response
        results = response.json()

        # Format the results nicely
        return format_results(results)

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to execute search: {str(e)}"


def format_results(results):
    """
    Format the search results into a readable string.

    Args:
        results: The search results from Serper API

    Returns:
        A formatted string with the search results
    """
    output = []

    # Add organic results
    if "organic" in results:
        output.append("SEARCH RESULTS:\n")

        for i, result in enumerate(results["organic"][:5], 1):
            title = result.get("title", "No title")
            link = result.get("link", "No link")
            snippet = result.get("snippet", "No description")

            output.append(f"{i}. {title}")
            output.append(f"   URL: {link}")
            output.append(f"   {snippet}")
            output.append("")

    # Add knowledge graph if available
    if "knowledgeGraph" in results:
        kg = results["knowledgeGraph"]
        output.append("KNOWLEDGE GRAPH:")
        output.append(f"Title: {kg.get('title', 'N/A')}")
        output.append(f"Type: {kg.get('type', 'N/A')}")
        if "description" in kg:
            output.append(f"Description: {kg['description']}")
        output.append("")

    # Add answer box if available
    if "answerBox" in results:
        ab = results["answerBox"]
        output.append("FEATURED SNIPPET:")
        if "title" in ab:
            output.append(f"Title: {ab['title']}")
        if "snippet" in ab:
            output.append(f"Snippet: {ab['snippet']}")
        if "answer" in ab:
            output.append(f"Answer: {ab['answer']}")
        output.append("")

    # Return the formatted output
    return "\n".join(output)


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simple web search using Serper API")
    parser.add_argument("query", type=str, nargs="+", help="The search query")
    parser.add_argument("--json", action="store_true", help="Return results as JSON")

    args = parser.parse_args()

    # Join query parts into a single string
    query = " ".join(args.query)

    # Set up and check API key
    api_key = setup()

    # Print start marker
    print("===BEGIN_RESULTS===")

    # Execute search
    start_time = time.time()
    results = search_serper(query, api_key)
    end_time = time.time()

    # Calculate execution time
    execution_time = end_time - start_time

    if args.json:
        # JSON output mode
        output = {"query": query, "results": results, "execution_time": execution_time}
        print(json.dumps(output, indent=2))
    else:
        # Regular text output mode
        print(f"Query: {query}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print("\n" + results)

    # Print end marker
    print("===END_RESULTS===")


if __name__ == "__main__":
    main()
