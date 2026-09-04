"""
FinGraph Case Intelligence & Collaboration Domain Exceptions.
"""

class CaseIntelligenceError(Exception):
    """Base domain exception for Case Intelligence operations."""
    pass


class CaseNotFoundError(CaseIntelligenceError):
    """Raised when a specified investigation case is not found."""
    pass


class CampaignNotFoundError(CaseIntelligenceError):
    """Raised when a specified fraud campaign is not found."""
    pass


class InvalidCollaboratorRoleError(CaseIntelligenceError):
    """Raised when an invalid collaborator role is requested."""
    pass


class UnauthorizedCollaborationError(CaseIntelligenceError):
    """Raised when a user lacks privileges to modify collaboration state."""
    pass


class CommentNotFoundError(CaseIntelligenceError):
    """Raised when a targeted case comment cannot be found."""
    pass
