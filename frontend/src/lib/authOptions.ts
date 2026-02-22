import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

// Defaults used when creating a user profile in the backend at registration time.
// These can be updated by the user later through the profile settings.
const DEFAULT_AGE = 30;
const DEFAULT_SEX = "unknown";

/**
 * Lightweight in-process credential store for the MVP.
 * Maps email → { userId, passwordHash }.
 *
 * TODO: Replace with a database-backed store before production use.
 * Limitations of the current approach:
 *  - All credentials are lost on server restart.
 *  - Incompatible with multi-instance deployments.
 * The PostgreSQL instance already in the stack is the recommended target.
 */
export const credentialStore = new Map<
  string,
  { userId: string; hash: string }
>();

export async function registerUser(
  email: string,
  password: string
): Promise<{ ok: boolean; userId?: string; error?: string }> {
  if (credentialStore.has(email)) {
    return { ok: false, error: "Email already registered" };
  }
  // Derive a readable prefix from the email local part, then append a
  // UUID-based suffix to guarantee global uniqueness.
  const atIndex = email.indexOf("@");
  const localPart = (atIndex > 0 ? email.slice(0, atIndex) : email)
    .replace(/[^A-Za-z0-9]/g, "_")
    .slice(0, 20);
  const userId = `${localPart}_${crypto.randomUUID().replace(/-/g, "").slice(0, 8)}`;

  // Mirror the user in the backend so the ML pipeline can track them.
  // If the backend is temporarily unreachable we proceed anyway — the
  // profile will be created on first authenticated API request.
  try {
    const res = await fetch(`${BACKEND}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        age: DEFAULT_AGE,
        sex: DEFAULT_SEX,
        migraine_history_years: 0,
        average_migraine_frequency: 0,
      }),
    });
    // 409 = already exists in backend, which is fine
    if (!res.ok && res.status !== 409) {
      console.warn(`[MVM] Backend user creation returned ${res.status} for ${userId}`);
    }
  } catch (err) {
    // Backend unreachable — log and continue; profile syncs on next request
    console.warn("[MVM] Could not reach backend during registration:", err);
  }
  const hash = await bcrypt.hash(password, 12);
  credentialStore.set(email, { userId, hash });
  return { ok: true, userId };
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email & Password",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        const record = credentialStore.get(credentials.email);
        if (!record) return null;
        const valid = await bcrypt.compare(credentials.password, record.hash);
        if (!valid) return null;
        return {
          id: record.userId,
          email: credentials.email,
          name: record.userId,
        };
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.userId = user.id;
      return token;
    },
    async session({ session, token }) {
      if (token.userId && session.user) {
        (session.user as { userId: string }).userId = token.userId as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
};
