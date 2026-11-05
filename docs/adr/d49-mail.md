# D49: Mail text, approved mailbox reads and plain-text sending

Status: amended on 1 November 2026 to allow explicitly approved plain-text sending.

## Context

Writing a message does not require access to someone's mailbox or authority to
send on their behalf. Reading and sending require separate, visible decisions.

## Decision

Keep ordinary mail drafting in the chat. Operators may enable
[private readers and mail submission](../private-readers.md). Mailbox reads still
require a manually unlocked [personal safe](../personal-safe.md) and approval for
each operation. Credentials stay outside the chat runtime.

`mail_send` permits one plain-text message after the person reviews the exact
sender, To/Cc/Bcc, subject and complete body, including their saved signature,
and explicitly clicks Send in the browser. The sender comes from the SSO account;
the signature is entered by the person in Settings and appended unchanged by the
manager. Missing signatures block submission. Signature or sender changes invalidate
pending approval. No directory-based or generated signature is substituted.

The disposable credential worker uses authenticated SMTP submission on port 587
with mandatory verified STARTTLS. The operator fixes the server and sender domain.
The tool cannot supply servers, sender identities, arbitrary headers or an HTML
body. Optional PDF attachments are read through the existing scoped file boundary
from the current project (5 files, 5 MiB total). File bytes are frozen before
approval; the browser displays names and sizes. Existing cloud share links stay
in the plain-text body; sending does not change cloud sharing permissions. Each approval is single-use and bound to the account, project,
session, browser claim and selected safe entry/version.

## Consequences

The popover closes after the outcome and reports server acceptance, refusal or
an uncertain result via toast. Acceptance is not proof of delivery. No automatic
retry follows a timeout or disconnect; a new submission needs fresh approval.
If any recipient is refused before DATA, the whole message is withheld.
No Sent-folder copy or mailbox draft is created. Users can still copy a draft
into their usual mail application when they need those features.

SMTP protocol fixtures and browser tests cover the flow without real recipients.
A real authenticated send is verified only after an explicitly approved test mail.
