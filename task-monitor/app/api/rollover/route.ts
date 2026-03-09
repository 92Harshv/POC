import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { rolloverIncompleteTasks } from "@/lib/rollover";

export async function POST(req: NextRequest) {
  // Allow cron secret or authenticated manager
  const cronSecret = req.headers.get("x-cron-secret");
  if (cronSecret !== process.env.CRON_SECRET) {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const user = session.user as { role: string };
    if (user.role !== "MANAGER") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
  }

  const result = await rolloverIncompleteTasks();
  return NextResponse.json(result);
}
