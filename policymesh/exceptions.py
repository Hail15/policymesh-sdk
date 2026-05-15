class PolicyMeshError(Exception):
    """Base exception for PolicyMesh SDK."""
    pass

class PolicyBlockedError(PolicyMeshError):
    """Raised when an action is blocked by policy."""
    def __init__(self, message, action_id=None, policy_matched=None):
        super().__init__(message)
        self.action_id = action_id
        self.policy_matched = policy_matched

class PolicyEscalateError(PolicyMeshError):
    """Raised when an action requires human approval."""
    def __init__(self, message, action_id=None, policy_matched=None):
        super().__init__(message)
        self.action_id = action_id
        self.policy_matched = policy_matched

class PolicyMeshConnectionError(PolicyMeshError):
    """Raised when the PolicyMesh API cannot be reached."""
    pass

class PolicyMeshAuthError(PolicyMeshError):
    """Raised when authentication fails."""
    pass