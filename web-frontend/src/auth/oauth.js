/**
 * OAuth 2.0 Authorization Code + PKCE flow implementation.
 * Tokens are kept in-memory (access token) and sessionStorage (code verifier).
 * Refresh tokens should be stored server-side via HttpOnly cookies in production.
 */

const OAUTH_CONFIG = {
  clientId: import.meta.env.VITE_OAUTH_CLIENT_ID || "quantumalpha-client",
  authorizationEndpoint:
    import.meta.env.VITE_OAUTH_AUTH_URL ||
    "https://auth.quantumalpha.example.com/authorize",
  tokenEndpoint:
    import.meta.env.VITE_OAUTH_TOKEN_URL ||
    "https://auth.quantumalpha.example.com/token",
  redirectUri:
    import.meta.env.VITE_OAUTH_REDIRECT_URI ||
    `${window.location.origin}/auth/callback`,
  scope: "openid profile email",
};

/** Generate a cryptographically random string for the PKCE code verifier */
const generateCodeVerifier = () => {
  const array = new Uint8Array(64);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) =>
    ("0" + (byte & 0xff).toString(16)).slice(-2),
  ).join("");
};

/** Derive the PKCE code challenge (S256) from the verifier */
const generateCodeChallenge = async (verifier) => {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
};

/**
 * Redirect the user to the OAuth authorization endpoint (PKCE flow).
 * Stores the code verifier in sessionStorage for retrieval on callback.
 */
export const initiateOAuthFlow = async () => {
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  const state = crypto.randomUUID();

  sessionStorage.setItem("oauth_code_verifier", codeVerifier);
  sessionStorage.setItem("oauth_state", state);

  const params = new URLSearchParams({
    response_type: "code",
    client_id: OAUTH_CONFIG.clientId,
    redirect_uri: OAUTH_CONFIG.redirectUri,
    scope: OAUTH_CONFIG.scope,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  });

  window.location.href = `${OAUTH_CONFIG.authorizationEndpoint}?${params}`;
};

/**
 * Handle the OAuth callback — exchange the authorization code for tokens.
 * @param {string} code - Authorization code from the callback URL
 * @param {string} returnedState - State parameter from callback URL
 * @returns {Promise<{accessToken: string, expiresIn: number}>}
 */
export const handleOAuthCallback = async (code, returnedState) => {
  const storedState = sessionStorage.getItem("oauth_state");
  const codeVerifier = sessionStorage.getItem("oauth_code_verifier");

  if (!storedState || returnedState !== storedState) {
    throw new Error("OAuth state mismatch — possible CSRF attack");
  }
  if (!codeVerifier) {
    throw new Error("Missing PKCE code verifier");
  }

  sessionStorage.removeItem("oauth_state");
  sessionStorage.removeItem("oauth_code_verifier");

  const response = await fetch(OAUTH_CONFIG.tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri: OAUTH_CONFIG.redirectUri,
      client_id: OAUTH_CONFIG.clientId,
      code_verifier: codeVerifier,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error_description || "Token exchange failed");
  }

  const data = await response.json();
  // Return access token for in-memory storage — do NOT persist to localStorage
  return {
    accessToken: data.access_token,
    expiresIn: data.expires_in,
    tokenType: data.token_type,
  };
};
