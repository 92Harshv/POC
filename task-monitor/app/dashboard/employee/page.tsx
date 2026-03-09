"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

interface Task {
  id: number;
  title: string;
  description?: string;
  status: string;
  dueDate: string;
  rolledOver: boolean;
}

export default function EmployeeDashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filterDate, setFilterDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  const fetchTasks = useCallback(async () => {
    const res = await fetch(`/api/tasks?date=${filterDate}`);
    if (res.ok) setTasks(await res.json());
  }, [filterDate]);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") fetchTasks();
  }, [status, fetchTasks]);

  async function toggleTask(task: Task) {
    const newStatus = task.status === "COMPLETED" ? "PENDING" : "COMPLETED";
    const res = await fetch(`/api/tasks/${task.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) fetchTasks();
  }

  const pending = tasks.filter((t) => t.status === "PENDING");
  const completed = tasks.filter((t) => t.status === "COMPLETED");
  const rolledOver = tasks.filter((t) => t.rolledOver && t.status === "PENDING");

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">My Tasks</h1>
            <p className="text-sm text-gray-500">{session?.user?.name}</p>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Progress ring + stats */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-500">Progress for</p>
              <input
                type="date"
                value={filterDate}
                onChange={(e) => setFilterDate(e.target.value)}
                className="mt-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <ProgressRing total={tasks.length} completed={completed.length} />
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">{pending.length}</p>
              <p className="text-xs text-gray-500">Pending</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{completed.length}</p>
              <p className="text-xs text-gray-500">Completed</p>
            </div>
            {rolledOver.length > 0 && (
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-500">{rolledOver.length}</p>
                <p className="text-xs text-gray-500">Rolled over</p>
              </div>
            )}
          </div>
        </div>

        {/* Task list */}
        {tasks.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm px-6 py-16 text-center text-gray-400">
            <p className="text-4xl mb-3">✓</p>
            <p className="font-medium">No tasks for this date.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <EmployeeTaskCard
                key={task.id}
                task={task}
                onToggle={toggleTask}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function EmployeeTaskCard({
  task,
  onToggle,
}: {
  task: Task;
  onToggle: (task: Task) => void;
}) {
  const isCompleted = task.status === "COMPLETED";

  return (
    <div
      className={`bg-white rounded-xl shadow-sm p-4 flex items-start gap-4 cursor-pointer transition-all hover:shadow-md ${
        isCompleted ? "opacity-60" : ""
      }`}
      onClick={() => onToggle(task)}
    >
      <div
        className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
          isCompleted
            ? "bg-green-500 border-green-500"
            : "border-gray-300"
        }`}
      >
        {isCompleted && (
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
            <path d="M10 3L5 8.5 2 5.5" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={`font-medium ${
            isCompleted ? "line-through text-gray-400" : "text-gray-900"
          }`}
        >
          {task.title}
          {task.rolledOver && !isCompleted && (
            <span className="ml-2 text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full">
              from yesterday
            </span>
          )}
        </p>
        {task.description && (
          <p className="text-sm text-gray-500 mt-0.5">{task.description}</p>
        )}
      </div>
      <span
        className={`text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0 ${
          isCompleted
            ? "bg-green-100 text-green-700"
            : "bg-yellow-100 text-yellow-700"
        }`}
      >
        {isCompleted ? "Done" : "To do"}
      </span>
    </div>
  );
}

function ProgressRing({
  total,
  completed,
}: {
  total: number;
  completed: number;
}) {
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100);
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative w-20 h-20 flex items-center justify-center">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r={radius}
          strokeWidth="8"
          stroke="#f3f4f6"
          fill="none"
        />
        <circle
          cx="40"
          cy="40"
          r={radius}
          strokeWidth="8"
          stroke="#22c55e"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <span className="absolute text-sm font-bold text-gray-900">{pct}%</span>
    </div>
  );
}
