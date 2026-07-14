CREATE TABLE `collection_history` (
`id` int AUTO_INCREMENT NOT NULL,
`userId` int NOT NULL,
`intent` varchar(32) NOT NULL,
`docCount` int NOT NULL DEFAULT 1,
`docSnippets` varchar(4000) NOT NULL DEFAULT '[]',
`individualSummaries` text NOT NULL,
`synthesisText` text NOT NULL,
`llmCalls` int NOT NULL DEFAULT 1,
`promptTokens` int NOT NULL DEFAULT 0,
`stages` varchar(200) NOT NULL DEFAULT 'collection',
`durationMs` int DEFAULT 0,
`model` varchar(128) DEFAULT 'gemini-2.5-flash',
`createdAt` timestamp NOT NULL DEFAULT (now()),
CONSTRAINT `collection_history_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `summary_history` ADD `model` varchar(128) DEFAULT 'gemini-2.5-flash';
