"""OData exceptions."""


class ODataError(Exception):
    """Base OData error."""

    pass


class ODataConnectionError(ODataError):
    """Connection failed."""

    pass


class ODataAuthError(ODataError):
    """Authentication failed."""

    pass
