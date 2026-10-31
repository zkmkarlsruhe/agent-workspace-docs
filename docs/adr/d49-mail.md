# D49: Produce mail text without mailbox access

Status: amended. Mailbox reads are optional and require browser approval; sending remains outside this decision.

## Context

Writing text for a message does not require access to someone's mailbox or
authority to send on their behalf.

## Decision

Provide message text in the chat for the person to copy. Do not provide sending
tools or the ability to create mailbox drafts.

An operator may enable [private readers](../private-readers.md). A person must
unlock their [personal safe](../personal-safe.md) and approve each mailbox read
in the browser. The worker uses the signed-in account name and the selected
secret for read-only IMAP access to the configured server. Credentials never
enter the chat runtime. No background mailbox polling is authorized by unlocking.

## Consequences

The person reviews and sends the text through their usual mail application.
There is no delivery automation. Optional read access adds encrypted credentials,
a temporary unlock lease and approval for each operation. Returned mail content
enters the chat and may reach its configured model provider. Sending would require
a separate decision, review flow and signature contract.
