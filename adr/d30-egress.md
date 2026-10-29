# D30: Restrict runtime egress

Status: accepted, with the current generic destination policy.

## Context

Programs and untrusted task content can cause unintended network requests,
including attempts to reach host services or other people's environments.

## Decision

Place each runtime on an internal network. Allow package-registry traffic
through an egress proxy. Expose web research, when enabled, through manager
tools that validate destinations and block private, loopback, link-local and
other protected address ranges. Apply service-specific checks to integrations.

## Consequences

Network policy is enforced outside the model. Legitimate tools needing wider
access require explicit integration work. Public requests still disclose URLs,
queries and possibly task content to recipients. Egress restrictions do not
eliminate prompt injection or malicious changes to local workspace files.
