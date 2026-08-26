# When to add Microsoft Foundry

## Prefer direct Fabric data agent to Microsoft 365 when

- the experience is read-only conversational analytics;
- the authoritative data is structured and already governed in Fabric;
- one Fabric data agent can answer the questions;
- user identity and underlying Fabric permissions should determine access;
- Teams or Microsoft 365 Copilot is the primary channel;
- a short path and low operational overhead are important.

For this demo, direct Fabric to M365 is enough for questions such as:

- current portfolio balance;
- arrears rate and 30+ delinquency;
- LVR distribution;
- first home buyer mix;
- application outcomes and channel performance.

## Prefer a Foundry layer when

- the solution must choose among multiple agents or tools;
- it combines Fabric analytics with unstructured policies or application
  documents;
- it needs custom orchestration, model choice, tracing, monitoring or cloud
  evaluation;
- it performs a longer workflow with human escalation;
- it must serve custom applications in addition to Microsoft 365;
- you need agent-specific safety evaluators such as prohibited actions and
  sensitive data leakage.

## Suggested FSI split

| Layer | Responsibility |
|---|---|
| Fabric data agent | Governed SQL-grounded portfolio analytics over OneLake. |
| Foundry agent | Route between portfolio data, policy retrieval, document processing and approved actions. |
| Workflow or case system | Manage state, approvals, records and operational actions. |
| Human credit officer | Own final high-impact lending decisions and exceptions. |

The Foundry agent should treat the Fabric data agent as the authoritative
structured-data tool. It should not reinterpret a portfolio aggregate as an
individual lending recommendation.

## Setup

1. Publish the Fabric data agent.
2. In a Foundry project, create a Microsoft Fabric connection using the Fabric
   workspace ID and data agent artifact ID.
3. Assign developers and users the required Foundry role.
4. Set:

```bash
export FOUNDRY_PROJECT_ENDPOINT="<project-endpoint>"
export FOUNDRY_MODEL_DEPLOYMENT_NAME="<model-deployment>"
export FABRIC_CONNECTION_NAME="<fabric-connection-name>"
```

5. Install and create the orchestrator:

```bash
pip install -r foundry/requirements.txt
python foundry/create_foundry_agent.py
```

6. Run the cloud evaluation:

```bash
export FOUNDRY_AGENT_NAME="home-loans-service-assistant"
python foundry/run_foundry_agent_evaluation.py
```

## Trade-offs

- Foundry adds an orchestration model that can reshape the Fabric result.
- It adds cost, latency, deployment, monitoring and support responsibilities.
- The Fabric and Foundry resources must be in the same tenant for the documented
  integration.
- Foundry consumption of Fabric data agent responses can move processing outside
  the Fabric compliance boundary or geography and is currently in preview.
- A Foundry layer does not remove the need for Fabric permissions, Purview,
  application controls, human oversight or FSI governance.

