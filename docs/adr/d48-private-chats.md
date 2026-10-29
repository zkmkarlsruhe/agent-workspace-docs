# D48: Share results, keep chats private between users

Status: accepted.

## Context

A task's useful result may be shareable while its conversation contains
personal context, intermediate mistakes or unrelated information.

## Decision

Do not provide chat sharing between users. People can download and pass on
results, or use a configured result-transfer integration.

## Consequences

Sharing a file does not grant product access to the source chat. People can
still copy or export their own conversation manually. Operators and backup
administrators can access stored data; optional evaluation also permits
authorized, audited transcript reads. Those accesses must be disclosed and
must not be described as user-to-user sharing.
