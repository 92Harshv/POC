export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const cron = await import("node-cron");
    const { rolloverIncompleteTasks } = await import("./lib/rollover");

    // Run at 11:59 PM every day to roll over incomplete tasks
    cron.schedule("59 23 * * *", async () => {
      console.log("[Cron] Running nightly task rollover...");
      const result = await rolloverIncompleteTasks();
      console.log(`[Cron] Rolled over ${result.rolledOver} tasks.`);
    });

    console.log("[Cron] Nightly task rollover scheduled.");
  }
}
