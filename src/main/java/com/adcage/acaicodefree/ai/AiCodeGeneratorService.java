package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.model.HtmlCodeResult;
import com.adcage.acaicodefree.ai.model.MutiFileCodeResult;
import dev.langchain4j.service.SystemMessage;

/**
 * AI生成服务
 * @author adcage
 * @description AiCodeGeneratorService
 * @createDate 2025/9/19 13:21
 */
public interface AiCodeGeneratorService {

    /**
     * 生成单个文件代码
     * @param userMessage 用户输入
     * @return 生成的代码
     */
    @SystemMessage(fromResource = "prompt/codegen-single-file-system-prompt.txt")
    HtmlCodeResult generateSingleFileCode(String userMessage);

    /**
     * 生成多个文件代码
     * @param userMessage 用户输入
     * @return 生成的代码
     */
    @SystemMessage(fromResource = "prompt/codegen-multi-file-system-prompt.txt")
    MutiFileCodeResult generateMultiFileCode(String userMessage);

}
