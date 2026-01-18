# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-17

### Added
- Initial release of sap-odata-python
- Full support for OData V2 (SAP Gateway) protocol
- Full support for OData V4 (RAP/CAP) protocol
- Unified `ODataClient` interface for both V2 and V4
- Fluent query builder with support for:
  - `$filter` - filtering entities
  - `$select` - selecting specific properties
  - `$expand` - expanding navigation properties
  - `$top` / `$skip` - pagination
  - `$orderby` - sorting
  - `$count` - counting entities
- Automatic CSRF token handling for write operations
- Metadata parsing with entity type inspection
- Batch operations support
- Response normalization across V2/V4 formats
- Comprehensive error handling with SAP-specific error messages
- Full type hints for IDE support
- Async/await support for high-performance applications
- Extensive documentation and examples

### Security
- Secure credential handling (no plaintext storage)
- SSL/TLS verification by default
- CSRF protection for state-changing operations

[Unreleased]: https://github.com/vaibhavgoel-github-1986/sap-odata-python/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/vaibhavgoel-github-1986/sap-odata-python/releases/tag/v1.0.0
