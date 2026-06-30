package com.adcage.acaicodefree.service;

/**
 * Python Agent Runtime 轻量标题生成桥接服务。
 */
public interface PythonTitleGenerationService {

    /**
     * 基于应用初始化需求生成应用名。
     *
     * @param initPrompt 应用初始化提示词
     * @param userId 当前用户 id
     * @return 应用标题
     */
    String generateAppTitle(String initPrompt, Long userId);

    /**
     * 基于会话上下文生成会话名。
     *
     * @param appName 应用名称
     * @param appInitPrompt 应用初始化提示词
     * @param firstUserMessage 会话首条用户消息
     * @param userId 当前用户 id
     * @return 会话标题
     */
    String generateSessionTitle(String appName, String appInitPrompt, String firstUserMessage, Long userId);
}
