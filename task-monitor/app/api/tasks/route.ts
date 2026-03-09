import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = session.user as { id: string; role: string };
  const { searchParams } = new URL(req.url);
  const date = searchParams.get("date");

  const where: Record<string, unknown> = {};

  if (user.role === "EMPLOYEE") {
    where.userId = parseInt(user.id);
  }

  if (date) {
    const start = new Date(date);
    start.setHours(0, 0, 0, 0);
    const end = new Date(date);
    end.setHours(23, 59, 59, 999);
    where.dueDate = { gte: start, lte: end };
  }

  const tasks = await prisma.task.findMany({
    where,
    include: { assignee: { select: { id: true, name: true, email: true } } },
    orderBy: { dueDate: "asc" },
  });

  return NextResponse.json(tasks);
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = session.user as { id: string; role: string };
  if (user.role !== "MANAGER") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const body = await req.json();
  const { title, description, userId, dueDate } = body;

  if (!title || !userId || !dueDate) {
    return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
  }

  const task = await prisma.task.create({
    data: {
      title,
      description,
      userId: parseInt(userId),
      dueDate: new Date(dueDate),
      createdBy: parseInt(user.id),
    },
    include: { assignee: { select: { id: true, name: true, email: true } } },
  });

  return NextResponse.json(task, { status: 201 });
}
