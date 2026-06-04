package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.TokenStream;
import dev.langchain4j.service.UserMessage;
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
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-single-file-system-prompt.txt")
    TokenStream generateSingleFileCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

    /**
     * 修改单个文件代码流
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-single-file-modify-system-prompt.txt")
    TokenStream modifySingleFileCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

    /**
     * 生成多个文件代码流
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-multi-file-system-prompt.txt")
    TokenStream generateMultiFileCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

    /**
     * 修改多文件代码流
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return 生成的代码流
     */
    @SystemMessage(fromResource = "prompt/codegen-multi-file-modify-system-prompt.txt")
    TokenStream modifyMultiFileCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

    /**
     * 生成 Vue 工程代码流（带工具调用事件）
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return TokenStream
     */
    @SystemMessage(fromResource = "prompt/codegen-vue-project-system-prompt.txt")
    TokenStream generateVueProjectCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

    /**
     * 修改 Vue 工程代码流（带工具调用事件）
     *
     * @param appId       应用 ID（记忆隔离）
     * @param userMessage 用户输入
     * @return TokenStream
     */
    @SystemMessage(fromResource = "prompt/codegen-vue-project-modify-system-prompt.txt")
    TokenStream modifyVueProjectCodeStream(@MemoryId Long appId, @UserMessage String userMessage);

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
