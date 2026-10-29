# D6: Per-person runtimes and hostnames

Status: accepted. Scope: the current browser deployment.

## Context

One OpenCode server can manage multiple projects and chats. Its web UI expects
its own origin rather than an arbitrary path prefix.

## Decision

Run one environment per active person and route a dedicated hostname to it.
Use the base domain for the portal. All requests pass through the manager's
identity and ownership checks. A foreign runtime hostname redirects the
authenticated person to the portal.

## Consequences

Deployment needs wildcard DNS and a certificate covering the base domain and
runtime hostnames. Stopping the environment preserves personal storage.
Projects belonging to one person share a runtime and are not separate security
boundaries. A hostname alone never grants access.
