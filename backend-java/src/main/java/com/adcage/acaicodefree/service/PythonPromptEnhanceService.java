package com.adcage.acaicodefree.service;

/**
 * Python Agent Runtime 提示词增强桥接服务。
 */
public interface PythonPromptEnhanceService {

    /**
     * 调用 Python Agent Runtime 增强提示词。
     *
     * @param prompt 原始提示词
     * @param userId 当前用户 id
     * @return 增强后的提示词
     */
    String enhancePrompt(String prompt, Long userId);
}
