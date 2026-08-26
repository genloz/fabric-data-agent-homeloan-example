#!/usr/bin/env python3
"""Create a Foundry orchestrator that uses the Fabric data agent as a tool."""

from __future__ import annotations

import os

from azure.ai.agents.models import FabricTool
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def main() -> None:
    project_client = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    connection = project_client.connections.get(
        os.environ["FABRIC_CONNECTION_NAME"]
    )
    fabric = FabricTool(connection_id=connection.id)
    instructions = """
You are the Home Loans Service Assistant.

Use the Microsoft Fabric tool for governed, read-only questions about the
synthetic home loans portfolio. Preserve the Fabric tool's stated filters,
denominators, currency, caveats, and refusal boundaries.

Do not make or recommend individual credit decisions, infer protected
attributes, provide personalised financial advice, or expose sensitive data.
For high-impact lending decisions, direct the user to approved credit policy
and qualified human review.
""".strip()

    with project_client:
        agent = project_client.agents.create_agent(
            model=os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"],
            name=os.getenv("FOUNDRY_AGENT_NAME", "home-loans-service-assistant"),
            instructions=instructions,
            tools=fabric.definitions,
        )
    print(f"Created Foundry agent: {agent.id}")
    print("Set FOUNDRY_AGENT_NAME and FOUNDRY_AGENT_ID for evaluation.")


if __name__ == "__main__":
    main()

