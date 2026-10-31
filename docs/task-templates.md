# Personal task templates

The start page links to **My task templates** (`/task-templates`). Definitions
belong to the signed-in account and are stored in the manager database. They are
available without optional integrations or a running workspace. Existing quick
starts remain available.

Create a template with a title, optional description and task text. Up to eight
named input fields can be short text, multiline text, a selection, yes/no, a date
or a number. Use `{{topic}}` to insert the field named `topic`. Values are inserted
literally once; expressions, scripts and nested substitutions are not evaluated.
This is text preparation, not a mechanism that makes instructions safe to execute.

Fields can be required. Each input is limited to 1000 characters; the rendered
task must contain 10–1000 characters. Selections have up to 20 distinct options,
each up to 100 characters. Numbers must be finite, between -1 billion and
1 billion, and within any configured minimum and maximum. Each account can keep
100 templates.

**Use template** opens the input form. **Preview task** renders the exact text
into the existing project start form. Choose project capabilities and knowledge
bases there, add files if needed, then start. The rendered text is read-only;
**Change inputs** returns to the form. Preview creates no project and starts no
chat. Starting validates the template revision and inputs again on the server.

Definitions have stable IDs and increasing revisions. A stale edit, deletion or
start is refused; reload the current template and review before retrying. There
is no revision restore, team sharing or scheduler. Export downloads the current
definition as JSON.

Project creation stores the exact definition revision, validated submitted
values and rendered task text atomically with the project. Attached filenames
are appended to the initial chat prompt by the normal upload flow and are not
part of the template rendering. Editing or deleting a template does not change
existing project provenance. Provenance follows the project through trash and
restore and is removed on permanent project purge. A project export includes
`task-submissions.json`; a full account export also includes
`task-templates.json`. Account deletion removes owned definitions and provenance.
Neither preview inputs nor provenance are copied to global audit logs.
