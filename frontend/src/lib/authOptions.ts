import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
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

/**
 * Tracks Google-authenticated users (email → userId).
 * Populated on first sign-in via Google.
 * Same MVP limitations as credentialStore above.
 */
export const googleUserStore = new Map<string, string>();

/** Generates a unique userId from an email address. */
function generateUserId(email: string): string {
  const atIndex = email.indexOf("@");
  const localPart = (atIndex > 0 ? email.slice(0, atIndex) : email)
    .replace(/[^A-Za-z0-9]/g, "_")
    .slice(0, 20);
  return `${localPart}_${crypto.randomUUID().replace(/-/g, "").slice(0, 8)}`;
}

/** Creates the user profile in the backend ML pipeline. */
async function createBackendUser(userId: string): Promise<void> {
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
    if (!res.ok && res.status !== 409) {
      console.warn(`[MVM] Backend user creation returned ${res.status} for ${userId}`);
    }
  } catch (err) {
    console.warn("[MVM] Could not reach backend during registration:", err);
  }
}

export async function registerUser(
  email: string,
  password: string
): Promise<{ ok: boolean; userId?: string; error?: string }> {
  if (credentialStore.has(email)) {
    return { ok: false, error: "Email already registered" };
  }
  const userId = generateUserId(email);
  await createBackendUser(userId);
  const hash = await bcrypt.hash(password, 12);
  credentialStore.set(email, { userId, hash });
  return { ok: true, userId };
}

export const authOptions: NextAuthOptions = {
  providers: [
    // GoogleProvider is only registered when credentials are configured.
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
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
    async signIn({ user, account }) {
      // For Google sign-ins, provision a backend user on first login.
      if (account?.provider === "google" && user.email) {
        if (!googleUserStore.has(user.email)) {
          const userId = generateUserId(user.email);
          await createBackendUser(userId);
          googleUserStore.set(user.email, userId);
        }
      }
      return true;
    },
    async jwt({ token, user, account }) {
      if (user) {
        // Credentials sign-in: userId is already on user.id
        token.userId = user.id;
      }
      if (account?.provider === "google" && token.email) {
        // Google sign-in: look up the provisioned userId (set in signIn callback)
        const userId = googleUserStore.get(token.email as string);
        if (userId) token.userId = userId;
      } else if (!token.userId && token.email) {
        // Subsequent requests for Google users: re-read from store
        const userId = googleUserStore.get(token.email as string);
        if (userId) token.userId = userId;
      }
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
