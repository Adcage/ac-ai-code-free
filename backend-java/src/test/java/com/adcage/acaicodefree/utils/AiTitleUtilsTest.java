package com.adcage.acaicodefree.utils;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AiTitleUtilsTest {

    @Test
    void fallbackAppTitleShouldStripPromptPrefix() {
        assertEquals("CRM 销售看板", AiTitleUtils.fallbackAppTitle("请帮我做一个 CRM 销售看板，支持线索分配"));
    }

    @Test
    void sanitizeTitleShouldUseFirstMeaningfulLine() {
        assertEquals("智能排班助手", AiTitleUtils.sanitizeAppTitle("标题：\"智能排班助手\"\n这是解释"));
    }

    @Test
    void defaultSessionTitleShouldBeRecognized() {
        assertTrue(AiTitleUtils.isDefaultSessionTitle("新会话 12"));
        assertFalse(AiTitleUtils.isDefaultSessionTitle("登录页优化"));
    }
}
