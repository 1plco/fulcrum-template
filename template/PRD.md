## Kick Start
- [ ] Read UNFURL.md and sop.md; understand requirement and decompose them into Task List section; NOTE: NEVER attempt to do all of the task at once. Find reasonable chunks to work on at any given time. 
- [ ] If we don't have any code yet but internal-db has tables; and the tables seem to be either empty or have test/sample data, please clean up (these are remenants of past unfurls that might've failed)

## Task List


## Completion Checklist

- [ ] All functions fully implemented (no stubs, no NotImplementedError)
- [ ] Migrations APPLIED (not just created)
- [ ] Make sure key information is dispatched back to user using skills/fulcrum-sdk
- [ ] Make sure functions are well integrated to internal-db
- [ ] Real data verification passes (no fake data patterns found); use browser-use for information that exist online
- [ ] Functions are composable and recoverable (idempotent, checkpointed, no hidden state)
- [ ] All validation commands pass (ruff format, ruff check, ty check, pytest)
- [ ] README.md documents all functions with SOP mappings