import { NextRequest, NextResponse } from "next/server";
import { registerUser } from "@/lib/authOptions";

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();

  if (!email || !password) {
    return NextResponse.json(
      { error: "email and password are required" },
      { status: 400 }
    );
  }

  const result = await registerUser(email, password);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 409 });
  }
  return NextResponse.json({ ok: true, userId: result.userId }, { status: 201 });
}
