"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

interface Task {
  id: number;
  title: string;
  description?: string;
  status: string;
  dueDate: string;
  rolledOver: boolean;
  assignee: { id: number; name: string; email: string };
  createdBy: number;
}

export default function ManagerDashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [filterDate, setFilterDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    userId: "",
    dueDate: new Date().toISOString().split("T")[0],
  });
  const [userForm, setUserForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "EMPLOYEE",
  });
  const [message, setMessage] = useState("");

  const fetchTasks = useCallback(async () => {
    const res = await fetch(`/api/tasks?date=${filterDate}`);
    if (res.ok) setTasks(await res.json());
  }, [filterDate]);

  const fetchUsers = useCallback(async () => {
    const res = await fetch("/api/users");
    if (res.ok) setUsers(await res.json());
  }, []);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
    const user = session?.user as { role?: string } | undefined;
    if (status === "authenticated" && user?.role !== "MANAGER")
      router.push("/dashboard/employee");
  }, [status, session, router]);

  useEffect(() => {
    if (status === "authenticated") {
      fetchTasks();
      fetchUsers();
    }
  }, [status, fetchTasks, fetchUsers]);

  async function createTask(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskForm),
    });
    if (res.ok) {
      setShowTaskForm(false);
      setTaskForm({
        title: "",
        description: "",
        userId: "",
        dueDate: new Date().toISOString().split("T")[0],
      });
      fetchTasks();
      flash("Task created successfully.");
    }
  }

  async function createUser(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userForm),
    });
    if (res.ok) {
      setShowUserForm(false);
      setUserForm({ name: "", email: "", password: "", role: "EMPLOYEE" });
      fetchUsers();
      flash("Team member added.");
    } else {
      const data = await res.json();
      flash(data.error || "Error creating user.");
    }
  }

  async function deleteTask(id: number) {
    if (!confirm("Delete this task?")) return;
    await fetch(`/api/tasks/${id}`, { method: "DELETE" });
    fetchTasks();
  }

  async function markComplete(id: number) {
    await fetch(`/api/tasks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "COMPLETED" }),
    });
    fetchTasks();
  }

  async function triggerRollover() {
    const res = await fetch("/api/rollover", { method: "POST" });
    const data = await res.json();
    flash(`Rolled over ${data.rolledOver} incomplete tasks.`);
    fetchTasks();
  }

  function flash(msg: string) {
    setMessage(msg);
    setTimeout(() => setMessage(""), 3000);
  }

  const employees = users.filter((u) => u.role === "EMPLOYEE");
  const pending = tasks.filter((t) => t.status === "PENDING");
  const completed = tasks.filter((t) => t.status === "COMPLETED");

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
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Task Monitor</h1>
            <p className="text-sm text-gray-500">
              Manager — {session?.user?.name}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowUserForm(true)}
              className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg"
            >
              + Add Member
            </button>
            <button
              onClick={() => setShowTaskForm(true)}
              className="text-sm bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg"
            >
              + New Task
            </button>
            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {message && (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm">
            {message}
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Team Members" value={employees.length} color="blue" />
          <StatCard label="Tasks Today" value={tasks.length} color="gray" />
          <StatCard label="Pending" value={pending.length} color="yellow" />
          <StatCard label="Completed" value={completed.length} color="green" />
        </div>

        {/* Date filter + rollover */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              Viewing date:
            </label>
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={triggerRollover}
            className="text-sm text-orange-600 hover:text-orange-800 border border-orange-200 hover:border-orange-400 px-3 py-1.5 rounded-lg"
          >
            Run Rollover Now
          </button>
        </div>

        {/* Task list */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">
              Tasks for {new Date(filterDate + "T12:00:00").toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </h2>
          </div>

          {tasks.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-400">
              No tasks for this date.
            </div>
          ) : (
            <ul className="divide-y divide-gray-50">
              {tasks.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onDelete={deleteTask}
                  onComplete={markComplete}
                />
              ))}
            </ul>
          )}
        </div>

        {/* Team section */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Team Members</h2>
          </div>
          {users.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-400">No users yet.</div>
          ) : (
            <ul className="divide-y divide-gray-50">
              {users.map((u) => (
                <li key={u.id} className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{u.name}</p>
                    <p className="text-sm text-gray-500">{u.email}</p>
                  </div>
                  <span
                    className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                      u.role === "MANAGER"
                        ? "bg-purple-100 text-purple-700"
                        : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {u.role}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>

      {/* Create Task Modal */}
      {showTaskForm && (
        <Modal title="New Task" onClose={() => setShowTaskForm(false)}>
          <form onSubmit={createTask} className="space-y-4">
            <FormField label="Title">
              <input
                type="text"
                value={taskForm.title}
                onChange={(e) =>
                  setTaskForm({ ...taskForm, title: e.target.value })
                }
                required
                className="input-field"
                placeholder="Task title"
              />
            </FormField>
            <FormField label="Description (optional)">
              <textarea
                value={taskForm.description}
                onChange={(e) =>
                  setTaskForm({ ...taskForm, description: e.target.value })
                }
                className="input-field min-h-[80px] resize-none"
                placeholder="Details..."
              />
            </FormField>
            <FormField label="Assign to">
              <select
                value={taskForm.userId}
                onChange={(e) =>
                  setTaskForm({ ...taskForm, userId: e.target.value })
                }
                required
                className="input-field"
              >
                <option value="">Select employee...</option>
                {employees.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Due date">
              <input
                type="date"
                value={taskForm.dueDate}
                onChange={(e) =>
                  setTaskForm({ ...taskForm, dueDate: e.target.value })
                }
                required
                className="input-field"
              />
            </FormField>
            <div className="flex gap-3 pt-2">
              <button type="submit" className="flex-1 btn-primary">
                Create Task
              </button>
              <button
                type="button"
                onClick={() => setShowTaskForm(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Add User Modal */}
      {showUserForm && (
        <Modal title="Add Team Member" onClose={() => setShowUserForm(false)}>
          <form onSubmit={createUser} className="space-y-4">
            <FormField label="Full name">
              <input
                type="text"
                value={userForm.name}
                onChange={(e) =>
                  setUserForm({ ...userForm, name: e.target.value })
                }
                required
                className="input-field"
                placeholder="Jane Smith"
              />
            </FormField>
            <FormField label="Email">
              <input
                type="email"
                value={userForm.email}
                onChange={(e) =>
                  setUserForm({ ...userForm, email: e.target.value })
                }
                required
                className="input-field"
                placeholder="jane@company.com"
              />
            </FormField>
            <FormField label="Password">
              <input
                type="password"
                value={userForm.password}
                onChange={(e) =>
                  setUserForm({ ...userForm, password: e.target.value })
                }
                required
                className="input-field"
                placeholder="Temporary password"
              />
            </FormField>
            <FormField label="Role">
              <select
                value={userForm.role}
                onChange={(e) =>
                  setUserForm({ ...userForm, role: e.target.value })
                }
                className="input-field"
              >
                <option value="EMPLOYEE">Employee</option>
                <option value="MANAGER">Manager</option>
              </select>
            </FormField>
            <div className="flex gap-3 pt-2">
              <button type="submit" className="flex-1 btn-primary">
                Add Member
              </button>
              <button
                type="button"
                onClick={() => setShowUserForm(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const colors: Record<string, string> = {
    blue: "text-blue-600",
    gray: "text-gray-700",
    yellow: "text-yellow-600",
    green: "text-green-600",
  };
  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colors[color]}`}>{value}</p>
    </div>
  );
}

function TaskRow({
  task,
  onDelete,
  onComplete,
}: {
  task: Task;
  onDelete: (id: number) => void;
  onComplete: (id: number) => void;
}) {
  const isCompleted = task.status === "COMPLETED";
  return (
    <li className="px-6 py-4 flex items-start gap-4">
      <input
        type="checkbox"
        checked={isCompleted}
        onChange={() => !isCompleted && onComplete(task.id)}
        className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
      />
      <div className="flex-1 min-w-0">
        <p
          className={`font-medium ${
            isCompleted ? "line-through text-gray-400" : "text-gray-900"
          }`}
        >
          {task.title}
          {task.rolledOver && (
            <span className="ml-2 text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full">
              rolled over
            </span>
          )}
        </p>
        {task.description && (
          <p className="text-sm text-gray-500 mt-0.5 truncate">
            {task.description}
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          Assigned to: {task.assignee.name}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            isCompleted
              ? "bg-green-100 text-green-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {task.status}
        </span>
        <button
          onClick={() => onDelete(task.id)}
          className="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none"
          title="Delete"
        >
          ×
        </button>
      </div>
    </li>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

function FormField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      {children}
    </div>
  );
}
