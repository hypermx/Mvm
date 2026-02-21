import { NextRequest, NextResponse } from "next/server";
import { registerUser } from "@/lib/authOptions";

export async function POST(req: NextRequest) {
  const { email, password, userId } = await req.json();

  if (!email || !password || !userId) {
    return NextResponse.json(
      { error: "email, password, and userId are required" },
      { status: 400 }
    );
  }

  const result = await registerUser(email, password, userId);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 409 });
  }
  return NextResponse.json({ ok: true }, { status: 201 });
}
