CREATE TABLE `summary_history` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`domain` varchar(32) NOT NULL,
	`inputSnippet` varchar(300) NOT NULL,
	`inputLength` int NOT NULL,
	`summaryText` text NOT NULL,
	`llmCalls` int NOT NULL DEFAULT 1,
	`promptTokens` int NOT NULL DEFAULT 0,
	`stages` varchar(200) NOT NULL DEFAULT 'single',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `summary_history_id` PRIMARY KEY(`id`)
);
