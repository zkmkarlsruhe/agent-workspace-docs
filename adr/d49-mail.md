# D49: Produce mail text without mailbox access

Status: accepted.

## Context

Writing text for a message does not require access to someone's mailbox or
authority to send on their behalf.

## Decision

Provide message text in the chat for the person to copy. Do not give the
helper mail access, sending tools or the ability to create mailbox drafts.

## Consequences

The person reviews and sends the text through their usual mail application.
There is no delivery automation or mail-account credential to manage. Adding
mailbox operations would be a new decision with a new authorization boundary.
