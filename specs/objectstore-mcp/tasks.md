# CONN-OBJECTSTORE-MCP — Implementation tasks

Governing spec: [spec.md](spec.md). Design: [plan.md](plan.md). Rows: [requirements.md](requirements.md).

Each task line reads `- [ ] T001 [P] [US1] <ID>-R012.4 description`. Tasks run producer first; a checked task has landed.

- [ ] T001 [US1] CONN-OBJECTSTORE-MCP-R002 Take the provider libraries from the SDK extras.
- [ ] T002 [US1] CONN-OBJECTSTORE-MCP-R001 Serve every store through the SDK backends.
- [ ] T003 [US2] CONN-OBJECTSTORE-MCP-R003 Accept WebDAV stores.
- [ ] T004 [P] CONN-OBJECTSTORE-MCP-R004 Name the SDK by its current name in every document.
- [ ] T005 [US3] CONN-OBJECTSTORE-MCP-R002.1 Ship every provider library in the served image.
- [ ] T006 [US3] CONN-OBJECTSTORE-MCP-R005 One typed tool per operation, and refusals that keep their cause.
- [ ] T007 [US3] CONN-OBJECTSTORE-MCP-R006 The safety governor wraps every tool's backend.
- [ ] T008 [US4] CONN-OBJECTSTORE-MCP-R007 Manage S3 bucket lifecycle, versioning and object tags.
- [ ] T009 [US4] CONN-OBJECTSTORE-MCP-R008 Package the complete surface.
