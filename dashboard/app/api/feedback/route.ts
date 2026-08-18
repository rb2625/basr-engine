import { NextResponse } from "next/server";
import { getClient } from "@/lib/supabase";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { name, email, message, page } = body;

    if (!message || typeof message !== "string" || message.trim().length < 3) {
      return NextResponse.json({ error: "Message is required" }, { status: 400 });
    }

    const supabase = getClient();
    const { error } = await supabase.from("feedback").insert({
      name: name || null,
      email: email || null,
      message: message.trim().slice(0, 2000),
      page: page || null,
    });

    if (error) {
      console.error("feedback insert error:", error.message);
      return NextResponse.json({ error: "Failed to save feedback" }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
