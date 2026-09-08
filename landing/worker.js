const BLOCK = new Set([
  "/wrangler.toml",
  "/wrangler.worker.toml",
  "/worker.js",
  "/readme.md",
  "/postship.md",
  "/package.json",
  "/package-lock.json",
  "/agents.md",
  "/claude.md",
]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();
    if (BLOCK.has(path) || path.endsWith(".toml") || path.endsWith(".jsonc")) {
      return new Response("Not found", { status: 404 });
    }
    return env.ASSETS.fetch(request);
  },
};
