"""
Batch - Batch request support for OData operations.
"""

from typing import TYPE_CHECKING, List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

if TYPE_CHECKING:
    from .service import ODataService


@dataclass
class BatchOperation:
    """
    Represents a single operation in a batch request.
    
    Attributes:
        method: HTTP method
        entity_path: Entity path
        data: Request body for POST/PUT/PATCH
        content_id: Content ID for referencing in changesets
    """
    method: str
    entity_path: str
    data: Optional[Dict[str, Any]] = None
    content_id: Optional[str] = None


@dataclass
class BatchResult:
    """
    Result of a batch operation.
    
    Attributes:
        content_id: Content ID of the operation
        status_code: HTTP status code
        data: Response data
        error: Error message if failed
    """
    content_id: str
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return 200 <= self.status_code < 300


class BatchRequest:
    """
    Batch request builder for executing multiple operations atomically.
    
    Supports OData $batch endpoint with changesets for atomic operations.
    
    Example:
        >>> with service.batch() as batch:
        ...     batch.get("Customers('CUST001')")
        ...     batch.create("Customers", {"Name": "New"})
        ...     batch.update("Customers('CUST002')", {"Name": "Updated"})
        >>> results = batch.execute()
    """
    
    def __init__(self, service: "ODataService") -> None:
        """Initialize batch request."""
        self._service = service
        self._operations: List[BatchOperation] = []
        self._changeset_operations: List[BatchOperation] = []
        self._content_id_counter = 1
    
    def _next_content_id(self) -> str:
        """Generate next content ID."""
        content_id = str(self._content_id_counter)
        self._content_id_counter += 1
        return content_id
    
    def get(self, entity_path: str) -> "BatchRequest":
        """
        Add a GET operation to the batch.
        
        Args:
            entity_path: Entity path to retrieve
        
        Returns:
            Self for chaining
        """
        self._operations.append(
            BatchOperation(
                method="GET",
                entity_path=entity_path,
                content_id=self._next_content_id(),
            )
        )
        return self
    
    def create(self, entity_path: str, data: Dict[str, Any]) -> "BatchRequest":
        """
        Add a POST (create) operation to the batch.
        
        Args:
            entity_path: Entity set path
            data: Entity data to create
        
        Returns:
            Self for chaining
        """
        self._changeset_operations.append(
            BatchOperation(
                method="POST",
                entity_path=entity_path,
                data=data,
                content_id=self._next_content_id(),
            )
        )
        return self
    
    def update(self, entity_path: str, data: Dict[str, Any]) -> "BatchRequest":
        """
        Add a PATCH (update) operation to the batch.
        
        Args:
            entity_path: Entity path with key
            data: Entity data to update
        
        Returns:
            Self for chaining
        """
        self._changeset_operations.append(
            BatchOperation(
                method="PATCH",
                entity_path=entity_path,
                data=data,
                content_id=self._next_content_id(),
            )
        )
        return self
    
    def delete(self, entity_path: str) -> "BatchRequest":
        """
        Add a DELETE operation to the batch.
        
        Args:
            entity_path: Entity path with key to delete
        
        Returns:
            Self for chaining
        """
        self._changeset_operations.append(
            BatchOperation(
                method="DELETE",
                entity_path=entity_path,
                content_id=self._next_content_id(),
            )
        )
        return self
    
    def execute(self) -> List[BatchResult]:
        """
        Execute the batch request.
        
        Returns:
            List of BatchResult objects
        """
        from .exceptions import ODataBatchError
        
        if not self._operations and not self._changeset_operations:
            return []
        
        # Build batch request body
        batch_boundary = f"batch_{uuid.uuid4().hex}"
        changeset_boundary = f"changeset_{uuid.uuid4().hex}"
        
        body_parts = []
        
        # Add GET operations (outside changeset)
        for op in self._operations:
            body_parts.append(f"--{batch_boundary}")
            body_parts.append("Content-Type: application/http")
            body_parts.append(f"Content-Transfer-Encoding: binary")
            body_parts.append("")
            body_parts.append(f"GET {self._service.url}/{op.entity_path} HTTP/1.1")
            body_parts.append("Accept: application/json")
            body_parts.append("")
        
        # Add changeset with write operations
        if self._changeset_operations:
            body_parts.append(f"--{batch_boundary}")
            body_parts.append(
                f"Content-Type: multipart/mixed; boundary={changeset_boundary}"
            )
            body_parts.append("")
            
            for op in self._changeset_operations:
                body_parts.append(f"--{changeset_boundary}")
                body_parts.append("Content-Type: application/http")
                body_parts.append("Content-Transfer-Encoding: binary")
                body_parts.append(f"Content-ID: {op.content_id}")
                body_parts.append("")
                body_parts.append(
                    f"{op.method} {self._service.url}/{op.entity_path} HTTP/1.1"
                )
                body_parts.append("Accept: application/json")
                body_parts.append("Content-Type: application/json")
                if op.data:
                    import json
                    body_parts.append("")
                    body_parts.append(json.dumps(op.data))
                body_parts.append("")
            
            body_parts.append(f"--{changeset_boundary}--")
        
        body_parts.append(f"--{batch_boundary}--")
        
        batch_body = "\r\n".join(body_parts)
        
        # Get CSRF token for batch
        csrf_token = self._service._client.get_csrf_token(self._service._full_path)
        
        # Execute batch request
        batch_url = f"{self._service.url}/$batch"
        headers = {
            "Content-Type": f"multipart/mixed; boundary={batch_boundary}",
            "Accept": "multipart/mixed",
            "X-CSRF-Token": csrf_token,
        }
        
        response = self._service._client._session.post(
            batch_url,
            data=batch_body,
            headers=headers,
            params={"sap-client": self._service._client.client},
            timeout=self._service._client.config.timeout,
        )
        
        if not response.ok:
            raise ODataBatchError(
                f"Batch request failed with status {response.status_code}"
            )
        
        # Parse batch response
        return self._parse_batch_response(response.text)
    
    def _parse_batch_response(self, response_text: str) -> List[BatchResult]:
        """Parse batch response into results."""
        # Simplified parsing - in production, use proper multipart parser
        results = []
        
        # This is a simplified implementation
        # A full implementation would parse the multipart response properly
        parts = response_text.split("--")
        
        content_id = "0"
        for part in parts:
            if "HTTP/1.1" in part:
                # Extract status code
                lines = part.strip().split("\n")
                for line in lines:
                    if "HTTP/1.1" in line:
                        status_str = line.split(" ")[1] if len(line.split(" ")) > 1 else "200"
                        try:
                            status_code = int(status_str)
                        except ValueError:
                            status_code = 200
                        
                        results.append(
                            BatchResult(
                                content_id=content_id,
                                status_code=status_code,
                            )
                        )
                        content_id = str(int(content_id) + 1)
                        break
        
        return results
    
    def __enter__(self) -> "BatchRequest":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        pass
    
    def __repr__(self) -> str:
        """String representation."""
        total_ops = len(self._operations) + len(self._changeset_operations)
        return f"BatchRequest(operations={total_ops})"
