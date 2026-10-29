# FreeCAD operator guide

FreeCAD runs one application per person. MCP tools and the browser share the
same visible document. The manager starts it on demand for a normal project.

## Setup

The public example uses linuxserver/freecad as an external runtime image. Its
image build files are GPL-3.0, FreeCAD is LGPL-2.1, and the Ubuntu base contains
packages under various licences. These components are not relicensed under MIT.
See the [licence inventory](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/THIRD_PARTY_LICENSES.md) and preserve upstream notices.

1. Build `services/freecad/Dockerfile` on the Docker host and publish it to your
   own registry. Set the same digest-pinned `OC_FREECAD_IMAGE` on the manager and
   Docker proxy. An empty value disables the application.
2. The example Compose `freecad` profile preloads that image. Run
   `docker compose --profile freecad up -d` from `deploy/example`.
3. Enable `integrations.freecad` in your instance, with `workspace:read` and
   `workspace:write` in `integration_grants.freecad`.
4. Enable the optional FreeCAD capability for the person and project.
5. Request `freecad_open` in the project chat. Poll after the returned delay
   while it reports `starting`, then open its authenticated `browser_url`.

The wildcard TLS and identity route must cover `cad-<session>.<workspace-domain>`.
No extra public application port is needed. The manager proxies HTTP and
WebSocket traffic. See the [tool schemas](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/services/freecad/tools.json) and
[application instructions](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/services/freecad/INSTRUCTIONS.md).

## Authority

`freecad_execute` runs unrestricted Python in the person's FreeCAD container.
Python is not sandboxed. The container mounts that person's stable `/workspace`.
Projects belonging to the same person are not filesystem security boundaries:
scripts can access the person's other projects. No other person's workspace or
Docker socket is mounted. Enable this capability only with that authority understood.

Revision checks, recovery copies, GUI input locking and undo transactions protect
normal edits. Arbitrary scripts can bypass helper checks, modify files or cause
side effects outside an undo transaction. Background scripts and workbench plugins
are not covered by a general concurrency guarantee. Uncertain writes are not replayed.

## Persistence and autosave limits

Native FCStd documents, exports, previews and recovery copies live in the project's
`freecad/` directory. `session.json` lists documents to restore. Container directories
`/config`, `/run` and `/tmp` are temporary. Back up the person's persistent workspace.

Autosave runs every 15 seconds, outside pending GUI transactions. A crash preserves
only the last successful save; later edits and active transactions can be lost.
`freecad_state` reports autosave errors. Normal close saves first; a pending GUI
edit can prevent it. Opening another project closes the previous application.
Stopping the environment, renaming or trashing its project also closes the session.

After a manager restart, stale containers are removed and saved documents restore
on the next open. Read current state again: document revisions and internal document
names can change. Account teardown or forced shutdown can discard unsaved work.
