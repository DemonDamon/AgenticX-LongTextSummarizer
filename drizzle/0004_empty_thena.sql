ALTER TABLE `collection_history` MODIFY COLUMN `docSnippets` varchar(4000) NOT NULL DEFAULT '[]';--> statement-breakpoint
ALTER TABLE `collection_history` MODIFY COLUMN `individualSummaries` text NOT NULL;--> statement-breakpoint
ALTER TABLE `collection_history` MODIFY COLUMN `synthesisText` text NOT NULL;