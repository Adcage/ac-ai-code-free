package com.adcage.acaicodefree.core;

import cn.hutool.core.util.StrUtil;

public final class VisualEditPromptHelper {

    private VisualEditPromptHelper() {
    }

    public static boolean isVisualEditRequest(String userMessage) {
        if (StrUtil.isBlank(userMessage)) {
            return false;
        }
        String normalized = userMessage.trim();
        return normalized.contains("选中元素信息：") && normalized.contains("修改需求：");
    }
}
