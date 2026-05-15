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

# Initialize with your org ID and API key
# Get your API key at https://policymesh.net → API Keys
client = PolicyMeshClient(
    org_id="your_org_id",
    api_key="your_api_key"
)

# Evaluate an agent action
decision = client.evaluate(
    agent_id="my_agent",
    action_type="data_export",
    data_classification="confidential",
    record_count=1500,
    description="Exporting customer records to external email"
)

print(decision.decision)       # "block"
print(decision.policy_matched) # "Sensitive Data Export Block"
print(decision.is_blocked)     # True
```

## Using the Guard Decorator

```python
from policymesh import PolicyMeshClient

client = PolicyMeshClient(
    org_id="your_org_id",
    api_key="your_api_key"
)

@client.guard(action_type="production_deploy", environment="production")
def deploy_to_production():
    print("Deploying to production...")

deploy_to_production()
```

## Simple Boolean Check

```python
if client.allow(agent_id="my_agent", action_type="data_access"):
    pass
```

## Handling Decisions

```python
from policymesh import PolicyMeshClient, PolicyBlockedError, PolicyEscalateError

client = PolicyMeshClient(
    org_id="your_org_id",
    api_key="your_api_key"
)

try:
    decision = client.evaluate(
        agent_id="my_agent",
        action_type="production_deploy",
        environment="production"
    )
    if decision.is_flagged:
        print("Action flagged but allowed.")
except PolicyBlockedError as e:
    print(f"Action blocked: {e.policy_matched}")
except PolicyEscalateError as e:
    print(f"Action requires approval: {e.policy_matched}")
```

## Action Types

| Action Type | Description |
|-------------|-------------|
| `data_export` | Exporting data to external systems |
| `data_access` | Accessing sensitive data |
| `data_delete` | Deleting data |
| `data_modify` | Modifying data |
| `external_email` | Sending emails to external addresses |
| `external_message` | Sending external messages |
| `webhook_call` | Calling webhooks |
| `production_deploy` | Deploying to production |
| `code_execution` | Executing code |
| `file_read` | Reading files |
| `file_write` | Writing files |
| `file_delete` | Deleting files |
| `permission_change` | Modifying permissions |
| `auth_change` | Changing authentication |
| `api_key_create` | Creating API keys |
| `payment` | Processing payments |
| `vendor_action` | Vendor operations |
| `external_api_call` | Calling external APIs |
| `web_browse` | Browsing the web |
| `web_scrape` | Scraping web content |
| `database_query` | Querying databases |
| `database_write` | Writing to databases |
| `database_delete` | Deleting from databases |
| `model_call` | Calling AI models |
| `prompt_injection` | Detected prompt injection |
| `custom` | Custom action types |

## Data Classifications

| Classification | Description |
|----------------|-------------|
| `public` | Publicly available data |
| `internal` | Internal company data |
| `confidential` | Confidential business data |
| `restricted` | Highly restricted or regulated data |

## Getting Your API Key

1. Sign in at [https://policymesh.net](https://policymesh.net)
2. Go to **API Keys** in the sidebar
3. Click **Generate Key**
4. Copy and save your key — it is shown only once

## Links

- [Dashboard](https://policymesh.net)
- [Documentation](https://policymesh.net)
- [GitHub](https://github.com/Hail15/policymesh-sdk)