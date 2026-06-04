package com.adcage.acaicodefree.ai.model;

import dev.langchain4j.model.output.structured.Description;
import lombok.*;

/**
 * 多文件代码结果
 * @author adcage
 * @description MultiFileCodeResult
 * @createDate 2025/9/25 16:22
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
@ToString
@Description("多文件前端网页代码结果")
public class MultiFileCodeResult {

    /**
     * HTML代码
     */
    @Description("HTML代码")
    private String htmlCode;

    /**
     * CSS代码
     */
    @Description("CSS代码")
    private String cssCode;

    /**
     * JS代码
     */
    @Description("JS代码")
    private String jsCode;

    /**
     * 描述
     */
    @Description("描述")
    private String description;
}
