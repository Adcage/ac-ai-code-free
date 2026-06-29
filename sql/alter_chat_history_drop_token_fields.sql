-- 从 chat_history 表移除已废弃的 token 字段（token 数据已迁移到 agent_run 表）
ALTER TABLE chat_history
    DROP COLUMN inputTokens,
    DROP COLUMN outputTokens;
