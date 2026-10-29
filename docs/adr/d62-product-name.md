# D62: Separate the product name from instance branding

Status: accepted.

## Context

A reusable project needs a name independent of its first deployment and of
the runtime it embeds.

## Decision

Call the product Agent Workspace. Describe OpenCode as its underlying runtime,
without using that upstream name as the product name. Configure deployment
names and branding through the instance.

## Consequences

Public documentation and examples can be reused across operators. A deployed
instance may use a different display name. The name decision does not assert
trademark clearance or reserve any domain.
