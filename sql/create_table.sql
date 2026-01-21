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