# D12: A dedicated Go manager

Status: accepted.

## Context

A general development-environment platform does not directly provide this
project's task portal, runtime routing, model mediation and account cleanup.

## Decision

Use a dedicated Go service for the portal, identity enforcement, environment
lifecycle, gateways and accounting. Keep OpenCode as the chat and execution
runtime. Store manager metadata in SQLite.

## Consequences

The deployment has a small central control service, but must maintain its
runtime API integration and lifecycle behavior. The manager is a sensitive
trust boundary and a single-host dependency. This choice does not provide
high availability or a stable third-party API.
