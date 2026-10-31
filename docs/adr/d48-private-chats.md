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

A newer general notice pauses collection and new automated evaluation until the
person accepts it. It does not remove already collected general chats from the
audited administrator view while that person's existing consent remains recorded.
Consent withdrawal, account deletion or blocking, evaluation-policy revocation
and support-profile privacy restrictions still deny access. A change to knowledge
indexing terms therefore does not make previously available general chats disappear.
