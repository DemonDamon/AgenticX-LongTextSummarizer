import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// Summary history table
export const summaryHistory = mysqlTable("summary_history", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  domain: varchar("domain", { length: 32 }).notNull(), // "email" | "news"
  inputSnippet: varchar("inputSnippet", { length: 300 }).notNull(),
  inputLength: int("inputLength").notNull(),
  summaryText: text("summaryText").notNull(),
  llmCalls: int("llmCalls").notNull().default(1),
  promptTokens: int("promptTokens").notNull().default(0),
  stages: varchar("stages", { length: 200 }).notNull().default("single"),
  durationMs: int("durationMs").default(0),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type SummaryHistory = typeof summaryHistory.$inferSelect;
export type InsertSummaryHistory = typeof summaryHistory.$inferInsert;
