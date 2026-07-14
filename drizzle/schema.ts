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

// Summary history table (single document)
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
  model: varchar("model", { length: 128 }).default("gemini-2.5-flash"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type SummaryHistory = typeof summaryHistory.$inferSelect;
export type InsertSummaryHistory = typeof summaryHistory.$inferInsert;

// Collection history table (multi-document)
export const collectionHistory = mysqlTable("collection_history", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  intent: varchar("intent", { length: 32 }).notNull(), // "compare" | "aggregate" | "timeline"
  docCount: int("docCount").notNull().default(1),
  // JSON array of {title, snippet} for each doc
  docSnippets: varchar("docSnippets", { length: 4000 }).notNull().default("[]"),
  // JSON array of individual summaries
  individualSummaries: text("individualSummaries").notNull(),
  // The cross-doc synthesis result
  synthesisText: text("synthesisText").notNull(),
  llmCalls: int("llmCalls").notNull().default(1),
  promptTokens: int("promptTokens").notNull().default(0),
  stages: varchar("stages", { length: 200 }).notNull().default("collection"),
  durationMs: int("durationMs").default(0),
  model: varchar("model", { length: 128 }).default("gemini-2.5-flash"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type CollectionHistory = typeof collectionHistory.$inferSelect;
export type InsertCollectionHistory = typeof collectionHistory.$inferInsert;
