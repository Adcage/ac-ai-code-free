-- 新增 isTestApp 字段，标记测试应用
ALTER TABLE app ADD COLUMN isTestApp TINYINT NOT NULL DEFAULT 0 COMMENT '是否测试应用：0-否，1-是';
