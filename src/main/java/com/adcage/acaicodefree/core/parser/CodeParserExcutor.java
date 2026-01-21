package com.adcage.acaicodefree.core.parser;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;

public class CodeParserExcutor {

    /**
     * 根据类型执行解析
     * @param content
     * @param codeGenTypeEnum
     * @return
     */
    public static Object excutePaser(String content, CodeGenTypeEnum codeGenTypeEnum) {
        return switch (codeGenTypeEnum) {
            case SINGLE_FILE -> new SingleFileParser().parseCode(content);
            case MULTI_FILE -> new MultiFileParser().parseCode(content);
            default -> throw new BusinessException(ErrorCode.SYSTEM_ERROR, "不支持的代码生成类型:" + codeGenTypeEnum);
        };
    }
}
