import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const user = session.user as { id: string; role: string };
  const body = await req.json();

  const task = await prisma.task.findUnique({ where: { id: parseInt(id) } });
  if (!task) {
    return NextResponse.json({ error: "Task not found" }, { status: 404 });
  }

  // Employees can only update their own tasks' status
  if (user.role === "EMPLOYEE") {
    if (task.userId !== parseInt(user.id)) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    const updated = await prisma.task.update({
      where: { id: parseInt(id) },
      data: { status: body.status },
      include: { assignee: { select: { id: true, name: true, email: true } } },
    });
    return NextResponse.json(updated);
  }

  // Managers can update any field
  const updated = await prisma.task.update({
    where: { id: parseInt(id) },
    data: {
      ...(body.title && { title: body.title }),
      ...(body.description !== undefined && { description: body.description }),
      ...(body.status && { status: body.status }),
      ...(body.dueDate && { dueDate: new Date(body.dueDate) }),
      ...(body.userId && { userId: parseInt(body.userId) }),
    },
    include: { assignee: { select: { id: true, name: true, email: true } } },
  });

  return NextResponse.json(updated);
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const user = session.user as { id: string; role: string };
  if (user.role !== "MANAGER") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  await prisma.task.delete({ where: { id: parseInt(id) } });
  return NextResponse.json({ success: true });
}
