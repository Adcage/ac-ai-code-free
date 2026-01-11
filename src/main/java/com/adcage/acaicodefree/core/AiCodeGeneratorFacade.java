package com.adcage.acaicodefree.core;

import com.adcage.acaicodefree.ai.AiCodeGeneratorService;
import com.adcage.acaicodefree.ai.model.HtmlCodeResult;
import com.adcage.acaicodefree.ai.model.MutiFileCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.io.File;

/**
 * AI代码生成门面类,组合代码生成和保存功能
 *
 * @author adcage
 * @description AiCodeGeneratorFacade
 */
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
        return switch (codeGenType) {
            case HTML -> generateAndSaveHtmlCode(userMessage);
            case MULTI_FILE -> generateAndSaveMutiFileCode(userMessage);
            default -> {
                String message = "不支持的生成代码类型" + codeGenType.getValue();
                throw new BusinessException(ErrorCode.PARAMS_ERROR, message);
            }
        };
    }

    /**
     * 生成并保存HTML代码
     * @param userMessage
     * @return
     */
    private File generateAndSaveHtmlCode(String userMessage) {
        HtmlCodeResult code = aiCodeGeneratorService.generateSingleFileCode(userMessage);
        return CodeFileSaver.saveHtmlCode(code);
    }

    /**
     * 生成并保存多文件代码
     * @param userMessage
     * @return
     */
    private File generateAndSaveMutiFileCode(String userMessage) {
        MutiFileCodeResult code = aiCodeGeneratorService.generateMultiFileCode(userMessage);
        return CodeFileSaver.saveMutiFileCode(code);
    }


}
