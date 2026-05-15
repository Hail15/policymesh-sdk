from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    DATA_EXPORT = "data_export"
    EXTERNAL_EMAIL = "external_email"
    PRODUCTION_DEPLOY = "production_deploy"
    PERMISSION_CHANGE = "permission_change"
    PAYMENT = "payment"
    DATA_ACCESS = "data_access"
    CUSTOM = "custom"


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Decision(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    ESCALATE = "escalate"
    BLOCK = "block"


@dataclass
class AgentAction:
    agent_id: str
    org_id: str
    action_type: ActionType
    data_classification: DataClassification = DataClassification.INTERNAL
    environment: str = "production"
    record_count: int = 0
    destination: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PolicyDecision:
    action_id: str
    agent_id: str
    org_id: str
    action_type: str
    decision: Decision
    policy_matched: Optional[str]
    would_have_blocked: bool
    message: str

    @property
    def is_allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    @property
    def is_blocked(self) -> bool:
        return self.decision == Decision.BLOCK

    @property
    def is_flagged(self) -> bool:
        return self.decision == Decision.FLAG

    @property
    def is_escalated(self) -> bool:
        return self.decision == Decision.ESCALATE