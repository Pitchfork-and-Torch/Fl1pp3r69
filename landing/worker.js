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

const CSP =
  "default-src 'self'; script-src 'self' https://hits.jonbailey.xyz; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://hits.jonbailey.xyz; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'";

const SECURITY_HEADERS = {
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
  "Content-Security-Policy": CSP,
};

function withSecurity(res) {
  const out = new Response(res.body, res);
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    out.headers.set(key, value);
  }
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();
    if (BLOCK.has(path) || path.endsWith(".toml") || path.endsWith(".jsonc")) {
      return withSecurity(new Response("Not found", { status: 404 }));
    }
    const res = await env.ASSETS.fetch(request);
    return withSecurity(res);
  },
};
