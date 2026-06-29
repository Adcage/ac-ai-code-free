-- 为 agent_run 表增加 token 用量字段，支持 Token 仪表盘统计
-- 每次 Agent 运行结束时通过 completeAgentRun gRPC 回传写入
ALTER TABLE agent_run
    ADD COLUMN inputTokens        INT DEFAULT 0 NOT NULL COMMENT '本次运行输入 token 总数' AFTER loopStateJson,
    ADD COLUMN outputTokens       INT DEFAULT 0 NOT NULL COMMENT '本次运行输出 token 总数' AFTER inputTokens,
    ADD COLUMN cacheReadTokens    INT DEFAULT 0 NOT NULL COMMENT '命中缓存的输入 token 数' AFTER outputTokens,
    ADD COLUMN cacheCreationTokens INT DEFAULT 0 NOT NULL COMMENT '写入缓存的 token 数' AFTER cacheReadTokens;

-- 给索引支持 Dashboard 按用户/时间聚合
ALTER TABLE agent_run
    ADD INDEX idx_user_time (userId, createTime);
