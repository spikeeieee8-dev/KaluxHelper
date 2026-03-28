import express from "express";
import cors from "cors";
import "./lib/db.js";

import authRoutes from "./routes/auth.js";
import statsRoutes from "./routes/stats.js";
import ticketsRoutes from "./routes/tickets.js";
import staffRoutes from "./routes/staff.js";
import moderationRoutes from "./routes/moderation.js";
import configRoutes from "./routes/config.js";

const app = express();
const PORT = process.env.API_PORT || 3001;

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/stats", statsRoutes);
app.use("/api/tickets", ticketsRoutes);
app.use("/api/staff", staffRoutes);
app.use("/api/moderation", moderationRoutes);
app.use("/api/config", configRoutes);

app.get("/api/health", (_req, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  console.log(`KaluxHost API Server running on port ${PORT}`);
});
