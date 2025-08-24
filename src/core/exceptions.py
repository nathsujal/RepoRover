"""
Custom exceptions for the RepoRover application.
"""
from typing import Any, Dict, Optional

from fastapi import status


class RepoRoverError(Exception):
    """Base exception class for RepoRover specific errors."""
    
    def __init__(
        self,
        detail: str = "An error occurred",
        error_code: str = "error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail)


class RepositoryError(RepoRoverError):
    """Raised when there's an error with repository operations."""
    
    def __init__(self, detail: str = "Repository error", **kwargs: Any) -> None:
        super().__init__(
            detail=detail,
            error_code="repository_error",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs,
        )


class AuthenticationError(RepoRoverError):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(
            detail=detail,
            error_code="authentication_error",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(RepoRoverError):
    """Raised when a user doesn't have permission to perform an action."""
    
    def __init__(self, detail: str = "Not authorized") -> None:
        super().__init__(
            detail=detail,
            error_code="authorization_error",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(RepoRoverError):
    """Raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            detail=detail,
            error_code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError(RepoRoverError):
    """Raised when input validation fails."""
    
    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(
            detail=detail,
            error_code="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitExceededError(RepoRoverError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded") -> None:
        super().__init__(
            detail=detail,
            error_code="rate_limit_exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class LLMError(RepoRoverError):
    """Raised when there's an error with the LLM service."""
    
    def __init__(self, detail: str = "LLM service error") -> None:
        super().__init__(
            detail=detail,
            error_code="llm_error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class AgentError(RepoRoverError):
    """Raised when there's an error in an agent's execution."""
    
    def __init__(self, detail: str = "Agent execution error") -> None:
        super().__init__(
            detail=detail,
            error_code="agent_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class VectorStoreError(RepoRoverError):
    """Raised when there's an error with the vector store."""
    
    def __init__(self, detail: str = "Vector store error") -> None:
        super().__init__(
            detail=detail,
            error_code="vector_store_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    