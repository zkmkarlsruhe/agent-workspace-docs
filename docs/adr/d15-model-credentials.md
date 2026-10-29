# D15: Keep model credentials in the gateway

Status: accepted.

## Context

A person can inspect and modify parts of their runtime. Provider credentials
placed there could be extracted and used outside the workspace's controls.

## Decision

Send model requests through a manager gateway. Keep gateway credentials in
the manager and provider credentials at the configured model gateway, outside
personal runtimes. Apply attribution, budget checks and metering there.

## Consequences

Runtime configuration contains the internal gateway endpoint rather than an
upstream secret. The manager and model gateway remain privileged. Current
attribution sends the username to LiteLLM, so it must be disclosed in the
instance privacy notice. Usage estimates do not guarantee provider billing.
