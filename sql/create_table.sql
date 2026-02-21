CREATE DATABASE IF NOT EXISTS ac_ai_code_free;

USE ac_ai_code_free;

-- 用户表
DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user
(
    id            BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    userAccount   VARCHAR(256)                           NOT NULL COMMENT '账号',
    userPassword  VARCHAR(512)                           NOT NULL COMMENT '密码',
    userName      VARCHAR(256)                           NULL COMMENT '用户昵称',
    userAvatar    VARCHAR(512)                           NULL COMMENT '用户头像',
    userProfile   VARCHAR(1024)                          NULL COMMENT '用户简介',
    userRole      VARCHAR(256) DEFAULT 'user'            NOT NULL COMMENT '用户角色：user/admin',
    editTime      DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '编辑时间',
    createTime    DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
    updateTime    DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    isDelete      TINYINT      DEFAULT 0                 NOT NULL COMMENT '是否删除',
    -- 会员相关信息，后续可以尝试单开表
    vipExpireTime DATETIME                               NULL COMMENT '会员过期时间',
    vipCode       VARCHAR(128)                           NULL COMMENT '会员兑换码',
    vipNumber     BIGINT                                 NULL COMMENT '会员编号',
    -- 用户邀请相关信息，后续可以尝试单开表
    shareCode     VARCHAR(20)                            NULL COMMENT '分享码',
    inviteUser    BIGINT                                 NULL COMMENT '邀请用户',
    UNIQUE KEY uk_userAccount (userAccount),
    INDEX idx_userName (userName)
) COMMENT '用户' COLLATE = utf8mb4_unicode_ci;



-- 应用表
DROP TABLE IF EXISTS app;
CREATE TABLE app
(
    id           BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    appName      VARCHAR(256)                       NULL COMMENT '应用名称',
    cover        VARCHAR(512)                       NULL COMMENT '应用封面',
    initPrompt   TEXT                               NULL COMMENT '应用初始化的 prompt',
    codeGenType  VARCHAR(64)                        NULL COMMENT '代码生成类型（枚举）',
    deployKey    VARCHAR(64)                        NULL COMMENT '部署标识',
    deployedTime DATETIME                           NULL COMMENT '部署时间',
    -- 99为精选应用，用于主页展示高质量的应用，使用整型而不是用枚举利于拓展
    priority     INT      DEFAULT 0                 NOT NULL COMMENT '优先级',
    userId       BIGINT                             NOT NULL COMMENT '创建用户id',
    editTime     DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '编辑时间',
    createTime   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
    updateTime   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    isDelete     TINYINT  DEFAULT 0                 NOT NULL COMMENT '是否删除',
    UNIQUE KEY uk_deployKey (deployKey), -- 确保部署标识唯一
    INDEX idx_appName (appName),         -- 提升基于应用名称的查询性能
    INDEX idx_userId (userId)            -- 提升基于用户 ID 的查询性能
) COMMENT '应用' COLLATE = utf8mb4_unicode_ci;
