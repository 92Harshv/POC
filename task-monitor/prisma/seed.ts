import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding database...");

  // Hash passwords
  const managerPw = await bcrypt.hash("manager123", 10);
  const emp1Pw = await bcrypt.hash("employee123", 10);
  const emp2Pw = await bcrypt.hash("employee123", 10);

  // Create manager
  const manager = await prisma.user.upsert({
    where: { email: "manager@company.com" },
    update: {},
    create: {
      name: "Alex Manager",
      email: "manager@company.com",
      password: managerPw,
      role: "MANAGER",
    },
  });

  // Create employees
  const emp1 = await prisma.user.upsert({
    where: { email: "alice@company.com" },
    update: {},
    create: {
      name: "Alice Johnson",
      email: "alice@company.com",
      password: emp1Pw,
      role: "EMPLOYEE",
    },
  });

  const emp2 = await prisma.user.upsert({
    where: { email: "bob@company.com" },
    update: {},
    create: {
      name: "Bob Smith",
      email: "bob@company.com",
      password: emp2Pw,
      role: "EMPLOYEE",
    },
  });

  // Create some tasks for today
  const today = new Date();
  today.setHours(12, 0, 0, 0);

  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  await prisma.task.createMany({
    data: [
      {
        title: "Review Q1 reports",
        description: "Go through the quarterly reports and summarize findings.",
        status: "PENDING",
        dueDate: today,
        userId: emp1.id,
        createdBy: manager.id,
      },
      {
        title: "Update client presentation",
        description: "Add new slides for the Thursday meeting.",
        status: "PENDING",
        dueDate: today,
        userId: emp1.id,
        createdBy: manager.id,
      },
      {
        title: "Fix login bug",
        description: "Investigate and resolve the reported login issue.",
        status: "COMPLETED",
        dueDate: today,
        userId: emp2.id,
        createdBy: manager.id,
      },
      {
        title: "Write API documentation",
        description: "Document all new endpoints added last sprint.",
        status: "PENDING",
        dueDate: today,
        userId: emp2.id,
        createdBy: manager.id,
        rolledOver: true,
      },
    ],
  });

  console.log("Seeded:");
  console.log("  Manager — manager@company.com / manager123");
  console.log("  Employee — alice@company.com / employee123");
  console.log("  Employee — bob@company.com / employee123");
  console.log("  4 sample tasks created for today");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
