# D59: Allowlisted central MCP tools

Status: accepted for shared read-only knowledge in the proof of concept.

## Context

A central MCP server can expose more tools than a workspace should offer,
and its inventory can change independently of a local deployment.

## Decision

Register central services through the catalog and gateway. Require a person's
opt-in for ordinary projects, or an Assistant's reviewed source grant, and an
explicit tool allowlist. Filter discovery and enforce that
allowlist on invocation. Keep the upstream credential in the manager; use
separate manager-side connections for personal service credentials.

## Consequences

New upstream tools are not automatically exposed. Existing native tool names
can be retained without inventing a universal knowledge API. Read-only access
still sends queries to another service, whose logging and retention require
review. A manifest is not proof that a remote service stores no personal data
or implements the future deletion contract.
