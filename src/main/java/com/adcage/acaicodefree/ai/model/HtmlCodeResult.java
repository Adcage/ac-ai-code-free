package com.adcage.acaicodefree.ai.model;

import dev.langchain4j.model.output.structured.Description;
import lombok.*;

/**
 * 单文件HTML代码生成结果
 * @author adcage
 * @description HtmlCodeResult
 * @createDate 2025/9/25 16:20
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
@ToString
@Description("单文件HTML代码生成结果")
public class HtmlCodeResult {

    /**
     * HTML代码
     */
    @Description("HTML代码")
    private String htmlCode;

    /**
     * HTML代码描述
     */
    @Description("HTML代码描述")
    private String description;
}
