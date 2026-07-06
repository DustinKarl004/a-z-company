// Decodes a JWT payload client-side WITHOUT verifying the signature.
// Only safe for UI routing/display — the backend is the source of truth for authorization.
export function decodeJwtPayload(token) {
  try {
    const [, payload] = token.split(".");
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}
