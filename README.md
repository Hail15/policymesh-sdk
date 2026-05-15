# PolicyMesh Python SDK

The official Python SDK for the [PolicyMesh](https://policymesh.net) AI Agent Control Platform.

**Agents propose. PolicyMesh enforces.**

## Installation

```bash
pip install policymesh
```

## Quick Start

```python
from policymesh import PolicyMeshClient

# Initialize the client with your org ID
client = PolicyMeshClient(org_id="your_org_id")

# Evaluate an agent action
decision = client.evaluate(
    agent_id="my_agent",
    action_type="data_export",
    data_classification="confidential",
    record_count=1500,
    description="Exporting customer records to external email"
)

print(decision.decision)      # "block"
print(decision.policy_matched) # "Sensitive Data Export Block"
print(decision.is_blocked)    # True
```

## Using the Guard Decorator

```python
from policymesh import PolicyMeshClient

client = PolicyMeshClient(org_id="your_org_id")

@client.guard(action_type="production_deploy", environment="production")
def deploy_to_production():
    # This function will be blocked if PolicyMesh says so
    print("Deploying to production...")

# If blocked, raises PolicyBlockedError before the function runs
deploy_to_production()
```

## Simple Boolean Check

```python
# Returns True if allowed, False if blocked
if client.allow(agent_id="my_agent", action_type="data_access"):
    # proceed with action
    pass
```

## Handling Decisions

```python
from policymesh import PolicyMeshClient, PolicyBlockedError, PolicyEscalateError

client = PolicyMeshClient(org_id="your_org_id")

try:
    decision = client.evaluate(
        agent_id="my_agent",
        action_type="production_deploy",
        environment="production"
    )
    if decision.is_flagged:
        print("Action flagged but allowed. Proceeding with caution.")
except PolicyBlockedError as e:
    print(f"Action blocked: {e.policy_matched}")
except PolicyEscalateError as e:
    print(f"Action requires approval: {e.policy_matched}")
```

## Action Types

| Action Type | Description |
|-------------|-------------|
| `data_export` | Exporting data to external systems |
| `external_email` | Sending emails to external addresses |
| `production_deploy` | Deploying to production environments |
| `permission_change` | Modifying user permissions or access |
| `payment` | Processing payments or vendor actions |
| `data_access` | Accessing sensitive data |
| `custom` | Custom action types |

## Data Classifications

| Classification | Description |
|----------------|-------------|
| `public` | Publicly available data |
| `internal` | Internal company data |
| `confidential` | Confidential business data |
| `restricted` | Highly restricted or regulated data |

## Links

- [Dashboard](https://policymesh.vercel.app)
- [Documentation](https://policymesh.net)
- [GitHub](https://github.com/Hail15/policymesh)