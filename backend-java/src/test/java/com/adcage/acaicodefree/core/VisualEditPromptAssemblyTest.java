package com.adcage.acaicodefree.core;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

class VisualEditPromptAssemblyTest {

    @Test
    void shouldRecognizeVisualEditPromptWhenContainsSelectionAndRequirement() {
        String prompt = """
                选中元素信息：
                - 页面路径：/
                - 标签：h1
                - 选择器：div.hero > h1
                - 当前内容：你好

                修改需求：把标题改成欢迎你
                """;

        Assertions.assertTrue(VisualEditPromptHelper.isVisualEditRequest(prompt));
    }

    @Test
    void shouldRejectNormalPromptWithoutSelectionInfo() {
        String prompt = "请把按钮颜色改成红色";

        Assertions.assertFalse(VisualEditPromptHelper.isVisualEditRequest(prompt));
    }
}
