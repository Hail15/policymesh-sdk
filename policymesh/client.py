import requests
from typing import Optional
from policymesh.models import AgentAction, PolicyDecision, Decision, ActionType, DataClassification
from policymesh.exceptions import (
    PolicyBlockedError,
    PolicyEscalateError,
    PolicyMeshConnectionError,
    PolicyMeshAuthError
)

DEFAULT_API_URL = "https://policymesh-production.up.railway.app/api/v1"

class PolicyMeshClient:
    """
    PolicyMesh Python SDK.

    Usage:
        from policymesh import PolicyMeshClient

        client = PolicyMeshClient(
            org_id="your_org_id",
            api_key="your_api_key"
        )

        decision = client.evaluate(
            agent_id="my_agent",
            action_type="data_export",
            data_classification="confidential",
            record_count=1500,
            description="Exporting customer records"
        )

        @client.guard(action_type="production_deploy", environment="production")
        def deploy_to_production():
            pass
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
        metadata: Optional[dict] = None
    ) -> PolicyDecision:
        """
        Evaluate an agent action against PolicyMesh policies.
        Returns a PolicyDecision object.
        Raises PolicyBlockedError if action is blocked and raise_on_block is True.
        Raises PolicyEscalateError if action is escalated and raise_on_escalate is True.
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
            "metadata": metadata or {}
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
                    "Generate API keys at https://policymesh.vercel.app"
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
        metadata: Optional[dict] = None
    ):
        """
        Decorator that wraps a function with PolicyMesh evaluation.
        If the action is blocked, the function will not execute.

        Usage:
            @client.guard(action_type="production_deploy", environment="production")
            def deploy():
                pass
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
                    metadata=metadata
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