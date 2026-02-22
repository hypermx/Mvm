import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/login",
  },
});

// Protect all routes except auth pages and static assets
export const config = {
  matcher: ["/((?!login|register|api/auth|api/register|_next|favicon.ico).*)"],
};
