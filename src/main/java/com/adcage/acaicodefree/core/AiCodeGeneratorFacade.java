package com.adcage.acaicodefree.core;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.ai.AiCodeGenServiceFactory;
import com.adcage.acaicodefree.ai.AiCodeGeneratorService;
import com.adcage.acaicodefree.ai.model.message.AiResponseMessage;
import com.adcage.acaicodefree.ai.model.message.ToolExecutedMessage;
import com.adcage.acaicodefree.ai.model.message.ToolRequestMessage;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.core.saver.CodeFileSaverExecutor;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import dev.langchain4j.service.tool.ToolExecution;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.FluxSink;

import java.io.File;

/**
 * AI代码生成门面类,组合代码生成和保存功能
 *
 * @author adcage
 * @description AiCodeGeneratorFacade
 */
@Slf4j
@Service
public class AiCodeGeneratorFacade {

    @Resource
    private AiCodeGenServiceFactory aiCodeGenServiceFactory;

    /**
     * 统一入口,生成并保存代码
     *
     * @param userMessage
     * @param codeGenType
     * @return
     */
    public File generateAndSaveCode(String userMessage, CodeGenTypeEnum codeGenType,Long appId) {
        if (codeGenType == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "生成代码类型不能为空");
        }
        AiCodeGeneratorService aiCodeGeneratorService = aiCodeGenServiceFactory.getService(appId, codeGenType);
        Object result = switch (codeGenType) {
            case SINGLE_FILE -> aiCodeGeneratorService.generateSingleFileCode(userMessage);
            case MULTI_FILE -> aiCodeGeneratorService.generateMultiFileCode(userMessage);
            default -> {
                String message = "不支持的生成代码类型" + codeGenType.getValue();
                throw new BusinessException(ErrorCode.PARAMS_ERROR, message);
            }
        };
        return CodeFileSaverExecutor.executeSaver(result, codeGenType,appId);
    }

    /**
     * 统一入口,生成并保存代码(流式)
     *
     * @param userMessage
     * @param codeGenType
     * @return
     */
    public Flux<String> generateAndSaveCodeStream(String userMessage, CodeGenTypeEnum codeGenType,Long appId) {
        if (codeGenType == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "生成代码类型不能为空");
        }
        AiCodeGeneratorService aiCodeGeneratorService = aiCodeGenServiceFactory.getService(appId, codeGenType);
        boolean modifyRequest = VisualEditPromptHelper.isVisualEditRequest(userMessage);
        Flux<String> codeStream = switch (codeGenType) {
            case SINGLE_FILE -> modifyRequest
                    ? aiCodeGeneratorService.modifySingleFileCodeStream(userMessage)
                    : aiCodeGeneratorService.generateSingleFileCodeStream(userMessage);
            case MULTI_FILE -> modifyRequest
                    ? aiCodeGeneratorService.modifyMultiFileCodeStream(userMessage)
                    : aiCodeGeneratorService.generateMultiFileCodeStream(userMessage);
            case VUE_PROJECT -> buildVueProjectMessageStream(aiCodeGeneratorService, appId, userMessage, modifyRequest);
            default -> {
                String message = "不支持的生成代码类型" + codeGenType.getValue();
                throw new BusinessException(ErrorCode.PARAMS_ERROR, message);
            }
        };
        if (codeGenType == CodeGenTypeEnum.VUE_PROJECT) {
            return codeStream;
        }
        // 委托给 Executor 处理解析与保存逻辑
        return CodeFileSaverExecutor.executeSaverStream(codeStream, codeGenType,appId);
    }

    private Flux<String> buildVueProjectMessageStream(AiCodeGeneratorService service,
                                                      Long appId,
                                                      String userMessage,
                                                      boolean modifyRequest) {
        return Flux.create(sink -> {
            try {
                if (modifyRequest) {
                    service.modifyVueProjectCodeStream(appId, userMessage)
                            .onNext(token -> handleToken(sink, token))
                            .onToolExecuted(toolExecution -> handleToolExecution(sink, toolExecution))
                            .onError(sink::error)
                            .onComplete(response -> sink.complete())
                            .start();
                    return;
                }
                service.generateVueProjectCodeStream(appId, userMessage)
                        .onNext(token -> handleToken(sink, token))
                        .onToolExecuted(toolExecution -> handleToolExecution(sink, toolExecution))
                        .onError(sink::error)
                        .onComplete(response -> sink.complete())
                        .start();
            } catch (Exception e) {
                sink.error(e);
            }
        }, FluxSink.OverflowStrategy.BUFFER);
    }

    private void handleToken(FluxSink<String> sink, String token) {
        if (sink.isCancelled() || StrUtil.isBlank(token)) {
            return;
        }
        sink.next(JSONUtil.toJsonStr(new AiResponseMessage(token)));
    }

    private void handleToolExecution(FluxSink<String> sink, ToolExecution toolExecution) {
        if (sink.isCancelled() || toolExecution == null || toolExecution.request() == null) {
            return;
        }
        String id = toolExecution.request().id();
        String name = toolExecution.request().name();
        String arguments = toolExecution.request().arguments();
        sink.next(JSONUtil.toJsonStr(new ToolRequestMessage(id, name, arguments)));
        sink.next(JSONUtil.toJsonStr(new ToolExecutedMessage(id, name, arguments, toolExecution.result())));
    }

}
