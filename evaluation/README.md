# Data agent evaluation

Use all three layers for a serious demonstration. They test different risks.

## 1. Native Fabric answer accuracy

The deterministic generator creates `ground_truth.csv` from the same committed
sample data. Run `run_fabric_accuracy_evaluation.py` from a Fabric notebook
environment with `fabric-data-agent-sdk` installed.

```bash
export FABRIC_DATA_AGENT_NAME=HomeLoansDataAgent
python evaluation/run_fabric_accuracy_evaluation.py
```

The Fabric evaluation creates summary and step tables and classifies responses
as correct, incorrect or unclear.

Recommended release gate:

- 100% of critical portfolio metrics correct;
- at least 90% overall accuracy;
- no unresolved incorrect answer for balance, rate, denominator or period.

## 2. Direct Fabric MCP responsible AI policy tests

Set the workspace and published data agent IDs:

```bash
export FABRIC_WORKSPACE_ID="<workspace-guid>"
export FABRIC_DATA_AGENT_ID="<data-agent-guid>"
python evaluation/run_mcp_policy_evaluation.py
```

The script checks:

- refusal to make individual lending decisions;
- refusal to infer protected attributes;
- absence of fabricated PII;
- personal financial advice boundaries;
- read-only behaviour;
- prompt injection resistance;
- grounded handling of missing fields;
- safe aggregation of hardship information.

The checks are deterministic smoke tests. High and critical cases still require
human review of the saved response text in `evaluation/results/`.

Recommended release gate:

- no critical failure;
- no sensitive data leakage;
- no fabricated protected attribute;
- no claim that a write or approval action was completed.

## 3. Optional Foundry cloud evaluation

If the architecture includes a Foundry orchestrator, run
`foundry/run_foundry_agent_evaluation.py`. The sample adds:

- coherence;
- hate and unfairness;
- violence and self-harm;
- prohibited actions;
- sensitive data leakage.

The prohibited actions and sensitive data leakage evaluators are agent-target
evaluators and are currently in preview.

## Additional FSI evaluation ideas

- Test row-level and column-level security with users in different access groups.
- Test that M365 users without Lakehouse access receive no data.
- Compare answers in Fabric, direct MCP, Foundry and Microsoft 365 to identify
  orchestration changes.
- Add approved lending-policy language to a custom rubric if a Foundry layer is
  used.
- Add regression questions for every business definition and every example
  query.
- Review logs and audit events for sensitive-query patterns.
- Perform formal model risk, privacy, legal and compliance review before any use
  with real customer or decisioning data.

