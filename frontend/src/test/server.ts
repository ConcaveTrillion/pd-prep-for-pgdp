// msw mock server — Node-side (jsdom test environment) request
// interception. Tests can call `server.use(...)` to register
// per-test handlers; the global `afterEach` in `setup.ts` resets
// them between tests so leaks are impossible.
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
