import { prisma } from "./prisma";

export async function rolloverIncompleteTasks() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  // Find all PENDING tasks due today or earlier
  const overdueTasks = await prisma.task.findMany({
    where: {
      status: "PENDING",
      dueDate: { lt: tomorrow },
    },
  });

  if (overdueTasks.length === 0) return { rolledOver: 0 };

  // Roll them over to tomorrow
  await prisma.task.updateMany({
    where: {
      id: { in: overdueTasks.map((t) => t.id) },
    },
    data: {
      dueDate: tomorrow,
      rolledOver: true,
    },
  });

  return { rolledOver: overdueTasks.length };
}
