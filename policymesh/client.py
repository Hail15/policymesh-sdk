import requests
from typing import Optional, List
from policymesh.models import AgentAction, PolicyDecision, Decision, ActionType, DataClassification
from policymesh.exceptions import (
    PolicyBlockedError,
    PolicyEscalateError,
    PolicyMeshConnectionError,
    PolicyMeshAuthError
)

DEFAULT_API_URL = "https://policymesh-production.up.railway.app/api/v1"

class TraceStep:
    """
    Represents a single step in an agent's execution trace.
    
    Usage:
        trace = [
            TraceStep(step=1, type="model_call", model="gpt-4", input="summarize data", output="querying db..."),
            TraceStep(step=2, type="tool_call", tool="database_query", output="1500 records returned"),
            TraceStep(step=3, type="action", input="export to email"),
        ]
    """
    def __init__(
        self,
        step: int,
        type: str,
        timestamp: Optional[str] = None,
        model: Optional[str] = None,
        tool: Optional[str] = None,
        input: Optional[str] = None,
        output: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None
    ):
        self.step = step
        self.type = type
        self.timestamp = timestamp
        self.model = model
        self.tool = tool
        self.input = input
        self.output = output
        self.duration_ms = duration_ms
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "step": self.step,
            "type": self.type,
            "timestamp": self.timestamp,
            "model": self.model,
            "tool": self.tool,
            "input": self.input,
            "output": self.output,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


class PolicyMeshClient:
    """
    PolicyMesh Python SDK.

    Usage:
        from policymesh import PolicyMeshClient, TraceStep

        client = PolicyMeshClient(
            org_id="your_org_id",
            api_key="your_api_key"
        )

        # Simple evaluation
        decision = client.evaluate(
            agent_id="my_agent",
            action_type="data_export",
            data_classification="confidential",
            record_count=1500
        )

        # With full agent trace
        decision = client.evaluate(
            agent_id="my_agent",
            action_type="data_export",
            trace=[
                TraceStep(step=1, type="model_call", model="gpt-4", input="user asked to export data"),
                TraceStep(step=2, type="tool_call", tool="database_query", output="1500 records found"),
                TraceStep(step=3, type="action", input="exporting to external email"),
            ]
        )
    """

    def __init__(
        self,
        org_id: str,
        api_key: str,
        api_url: str = DEFAULT_API_URL,
        raise_on_block: bool = True,
        raise_on_escalate: bool = False
    ):
        self.org_id = org_id
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.raise_on_block = raise_on_block
        self.raise_on_escalate = raise_on_escalate

    def evaluate(
        self,
        agent_id: str,
        action_type: str,
        data_classification: str = "internal",
        environment: str = "production",
        record_count: int = 0,
        destination: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        trace: Optional[List[TraceStep]] = None
    ) -> PolicyDecision:
        """
        Evaluate an agent action against PolicyMesh policies.
        Optionally include a trace of the agent's execution chain.
        """
        payload = {
            "agent_id": agent_id,
            "org_id": self.org_id,
            "action_type": action_type,
            "data_classification": data_classification,
            "environment": environment,
            "record_count": record_count,
            "destination": destination,
            "description": description,
            "metadata": metadata or {},
            "trace": [t.to_dict() for t in trace] if trace else []
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.api_url}/evaluate",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 401:
                raise PolicyMeshAuthError(
                    "Authentication failed. Check your api_key and org_id. "
                    "Generate API keys at https://policymesh.net"
                )

            if response.status_code == 429:
                raise PolicyMeshConnectionError(
                    f"Rate limit exceeded: {response.json().get('detail', 'Monthly action limit reached.')}"
                )

            if response.status_code != 200:
                raise PolicyMeshConnectionError(
                    f"PolicyMesh API returned {response.status_code}: {response.text}"
                )

            data = response.json()
            decision = PolicyDecision(
                action_id=data["action_id"],
                agent_id=data["agent_id"],
                org_id=data["org_id"],
                action_type=data["action_type"],
                decision=Decision(data["decision"]),
                policy_matched=data.get("policy_matched"),
                would_have_blocked=data.get("would_have_blocked", False),
                message=data.get("message", "")
            )

            if self.raise_on_block and decision.is_blocked:
                raise PolicyBlockedError(
                    f"Action blocked by PolicyMesh: {decision.policy_matched}",
                    action_id=decision.action_id,
                    policy_matched=decision.policy_matched
                )

            if self.raise_on_escalate and decision.is_escalated:
                raise PolicyEscalateError(
                    f"Action requires approval: {decision.policy_matched}",
                    action_id=decision.action_id,
                    policy_matched=decision.policy_matched
                )

            return decision

        except (PolicyBlockedError, PolicyEscalateError, PolicyMeshAuthError):
            raise
        except requests.exceptions.ConnectionError:
            raise PolicyMeshConnectionError(
                "Could not connect to PolicyMesh API. Check your network connection."
            )
        except requests.exceptions.Timeout:
            raise PolicyMeshConnectionError(
                "PolicyMesh API timed out. Try again or check your connection."
            )
        except Exception as e:
            raise PolicyMeshConnectionError(f"Unexpected error: {e}")

    def guard(
        self,
        action_type: str,
        agent_id: str = "sdk_agent",
        data_classification: str = "internal",
        environment: str = "production",
        record_count: int = 0,
        destination: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        trace: Optional[List[TraceStep]] = None
    ):
        """
        Decorator that wraps a function with PolicyMesh evaluation.
        Supports trace for full agent execution chain visibility.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                decision = self.evaluate(
                    agent_id=agent_id,
                    action_type=action_type,
                    data_classification=data_classification,
                    environment=environment,
                    record_count=record_count,
                    destination=destination,
                    description=description or f"Calling {func.__name__}",
                    metadata=metadata,
                    trace=trace
                )
                if decision.is_blocked:
                    raise PolicyBlockedError(
                        f"Function {func.__name__} blocked by PolicyMesh: {decision.policy_matched}",
                        action_id=decision.action_id,
                        policy_matched=decision.policy_matched
                    )
                if self.raise_on_escalate and decision.is_escalated:
                    raise PolicyEscalateError(
                        f"Function {func.__name__} requires approval: {decision.policy_matched}",
                        action_id=decision.action_id,
                        policy_matched=decision.policy_matched
                    )
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def allow(self, agent_id: str, action_type: str, **kwargs) -> bool:
        """
        Simple boolean check. Returns True if allowed, False if blocked or escalated.
        Never raises exceptions.
        """
        try:
            decision = self.evaluate(agent_id=agent_id, action_type=action_type, **kwargs)
            return decision.is_allowed or decision.is_flagged
        except Exception:
            return True