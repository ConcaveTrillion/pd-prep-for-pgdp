// Default msw handlers shared across the test suite.
//
// Empty by design for the toolchain bring-up tick: roadmap §9 step 1
// only wires the harness. Handlers for the three target flows
// (create-project, page-tagger bulk actions, workbench drag-create)
// land in subsequent ticks alongside the tests that need them. Tests
// that need request interception today should register their own
// handlers via `server.use(...)`.
import type { RequestHandler } from "msw";

export const handlers: RequestHandler[] = [];
