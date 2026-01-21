package com.adcage.acaicodefree.core;

import com.adcage.acaicodefree.ai.AiCodeGeneratorService;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.core.saver.CodeFileSaverExecutor;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

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
    private AiCodeGeneratorService aiCodeGeneratorService;

    /**
     * 统一入口,生成并保存代码
     *
     * @param userMessage
     * @param codeGenType
     * @return
     */
    public File generateAndSaveCode(String userMessage, CodeGenTypeEnum codeGenType) {
        if (codeGenType == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "生成代码类型不能为空");
        }
        Object result = switch (codeGenType) {
            case SINGLE_FILE -> aiCodeGeneratorService.generateSingleFileCode(userMessage);
            case MULTI_FILE -> aiCodeGeneratorService.generateMultiFileCode(userMessage);
            default -> {
                String message = "不支持的生成代码类型" + codeGenType.getValue();
                throw new BusinessException(ErrorCode.PARAMS_ERROR, message);
            }
        };
        return CodeFileSaverExecutor.executeSaver(result, codeGenType);
    }

    /**
     * 统一入口,生成并保存代码(流式)
     *
     * @param userMessage
     * @param codeGenType
     * @return
     */
    public Flux<String> generateAndSaveCodeStream(String userMessage, CodeGenTypeEnum codeGenType) {
        if (codeGenType == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "生成代码类型不能为空");
        }
        Flux<String> codeStream = switch (codeGenType) {
            case SINGLE_FILE -> aiCodeGeneratorService.generateSingleFileCodeStream(userMessage);
            case MULTI_FILE -> aiCodeGeneratorService.generateMultiFileCodeStream(userMessage);
            default -> {
                String message = "不支持的生成代码类型" + codeGenType.getValue();
                throw new BusinessException(ErrorCode.PARAMS_ERROR, message);
            }
        };
        // 委托给 Executor 处理解析与保存逻辑
        return CodeFileSaverExecutor.executeSaver(codeStream, codeGenType);
    }

}
