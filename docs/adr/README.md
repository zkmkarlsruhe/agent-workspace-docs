# Decision reference index

This index preserves the decision numbers found in the manager's Go sources;
the summaries describe the original rationale, not new deployment requirements.

- D1: Review the plan before implementation so the design can be checked before code is built.
- D3: Reuse the existing identity provider because the operating team can manage it.
- D8: Keep runtime authentication behind the manager so people do not face a second login prompt.
- D11: Initialize version control in each project because snapshot undo requires a repository.
- D13: Separate standard, optional and personal capabilities so administrators can set defaults while people choose additions.
- D14: Keep personal skills persistent and writable so people can retain and refine their own workflows.
- D15: Keep provider configuration and credentials outside personal runtimes while allowing people to adjust permitted configuration; the manager gateway supplies credentials.
- D16: Use one upstream model key in the manager and pass identity through a request header instead of issuing per-person keys.
- D25: Keep office conversion out of the runtime image and plan a shared, metered conversion service; until then, spreadsheets include result values alongside formulas that recalculate on opening.
- D29: Mediate web reads through the manager with URL provenance, caching, sanitization, untrusted-content marking and source logs; use browser rendering only when required and document conversion for PDFs.
- D30: Restrict container egress to package sources and mediate web access through manager tools to protect internal services; later policy permits public institutional addresses while retaining private-network protections ([ADR](d30-egress.md)).
- D33: Separate privileged storage provisioning from ordinary file access to limit the manager's direct host filesystem privileges ([ADR](d33-provisioner.md)).
- D37: Build a small demonstration with early egress controls and quotas, deferring additional services until user feedback establishes their value.
- D38: Set explicit storage, upload and session limits and provide initial task templates to keep the demonstration bounded and usable.
- D44: Share a remapped container UID range to avoid repeated image copying and ownership changes while keeping runtime operations maintainable ([ADR](d44-docker.md)).
- D47: Reuse the connected file service's folder permissions for knowledge collections instead of building a separate sharing system, with writes subsequently restricted by D58.
- D50: Follow the browser language so branding does not override the person's language choice.
- D51: Load only catalog MCP servers so credentials and outbound access remain under manager control.
- D53: Include presentation generation in the runtime and catalog so people can create slide decks.
- D54: Allow execution in runtime temporary storage because file watchers and live configuration reload require it.
- D56: Admit active accounts without an additional group restriction so the prototype is accessible after mandatory consent, within usage and concurrency limits.
- D58: Enforce cloud-file access in the manager because account-wide credentials require a central boundary that restricts writes to a transfer folder, protects user changes and forbids deletion ([ADR](d58-cloud-files.md)).
- D59: Route shared read-only knowledge tools through a central gateway with explicit tool allowlists and per-request opt-in checks so credentials remain outside personal runtimes ([ADR](d59-central-mcp.md)).
- D60: Run optional tools in restricted containers without network access so extra programs can use the person's workspace without gaining the main runtime's connectivity ([ADR](d60-toolboxes.md)).
- D61: Expose room and equipment availability as read-only tools because cancelling a booking would permanently delete data.

Planning references in source comments refer to internal documents that are not
part of the public tree:

- `blueprint/01`: This was an internal identity and routing planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/02`: This was an internal manager and lifecycle planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/03`: This was an internal storage and provisioning planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/04`: This was an internal model gateway and metering planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/05`: This was an internal tool gateway planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/06`: This was an internal capability catalog planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/07`: This was an internal portal and project workflow planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/10`: This was an internal web research planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `blueprint/12`: This was an internal service integration planning document; the relevant public content is in [docs/architecture.md](../architecture.md).
- `research/09`: This was an internal usage and environmental estimation planning document, including sections B.1 and B.2.1–B.2.4; the relevant public content is in [docs/architecture.md](../architecture.md).
- `research/05`: Configuration and capability catalogs separate permitted personal settings from provider credentials; base skills take precedence over personal skills with the same ID (D13–D16, D51).
- `design/DESIGN.md`: The portal uses a project identity, system fonts, light and dark themes, a single accent, plain labels, visible focus and progressive enhancement. The embedded chat UI retains its own typography and layout. Production templates remain authoritative.
