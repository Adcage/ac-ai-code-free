package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import dev.langchain4j.service.SystemMessage;
import reactor.core.publisher.Flux;

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
    SingleCodeResult generateSingleFileCode(String userMessage);

    /**
     * 生成多个文件代码
     * @param userMessage 用户输入
     * @return 生成的代码
     */
    @SystemMessage(fromResource = "prompt/codegen-multi-file-system-prompt.txt")
    MultiFileCodeResult generateMultiFileCode(String userMessage);

    /**
     * 生成单个文件代码流
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-single-file-system-prompt.txt")
    Flux<String> generateSingleFileCodeStream(String userMessage);

    /**
     * 生成多个文件代码流
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-multi-file-system-prompt.txt")
    Flux<String> generateMultiFileCodeStream(String userMessage);

    /**
     * 聊天
     * @param userMessage 用户输入
     * @return 聊天结果
     */
    String chat(String userMessage);

    /**
     * 聊天
     * @param userMessage 用户输入
     * @return 聊天的代码流
     */
    Flux<String> chatStream(String userMessage);
}
