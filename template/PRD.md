## Kickstart Tasks (Please check these off if complete)
- [ ] Read UNFURL.md and sop.md; understand requirements and decompose them into the Main Task List section as blocks of logical, independent tasks — NOT fine-grained implementation sub-tasks. Each task block should represent a coherent unit of work (e.g. "Implement invoice extraction pipeline" not "Create model" + "Write parser" + "Add validation" + "Write test" as separate items). NOTE: NEVER attempt to do all tasks at once. Work through one logical block at a time. No need to add additional verification at the end because we already have a Completion Checklist section
- [ ] If we don't have any code yet but internal-db has tables; and the tables seem to be either empty or have test/sample data, please delete those tables (these are remenants of past unfurls that might've failed)
- [ ] Check if reference data in `resources/` needs to be loaded into internal-db tables; if tables should contain data from resource files, populate them. Do NOT leave tables empty if functions depend on that data.
- [ ] IMPORTANT: Tests MUST NOT write to internal-db. If database tests are needed, stage transactions without committing (dry run) and check output — never insert test rows.

## Main Task List


## Completion Checklist Tasks

- [ ] All functions fully implemented (no stubs, no NotImplementedError)
- [ ] Migrations APPLIED (not just created)
- [ ] Make sure key information is dispatched back to user using skills/fulcrum-sdk; make sure only key results and summaries are dispatched and will not result in thousands of messages.
- [ ] Make sure functions are well integrated to internal-db
- [ ] Real data verification passes (no fake data patterns found); use browser-use for information that exist online
- [ ] Functions are composable and recoverable (idempotent, checkpointed, no hidden state)
- [ ] All validation commands pass (ruff format, ruff check, ty check, pytest)
- [ ] README.md documents all functions with SOP mappings