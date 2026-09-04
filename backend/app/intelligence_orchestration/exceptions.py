"""
FinGraph Intelligence Orchestration Domain Exceptions.
"""

class OrchestrationError(Exception):
    """Base exception for intelligence orchestration domain."""
    pass


class TaskNotFoundError(OrchestrationError):
    """Raised when an investigation task is not found."""
    pass


class InvalidWorkflowTransitionError(OrchestrationError):
    """Raised when an illegal workflow state transition is attempted."""
    pass


class TemplateNotFoundError(OrchestrationError):
    """Raised when a workflow template specification is not found."""
    pass


class BriefGenerationError(OrchestrationError):
    """Raised when investigation brief synthesis fails."""
    pass
