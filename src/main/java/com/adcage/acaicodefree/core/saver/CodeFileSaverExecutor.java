package com.adcage.acaicodefree.core.saver;

import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.core.parser.CodeParserExcutor;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

import java.io.File;

@Slf4j
public class CodeFileSaverExecutor {
    private static final SingleCodeFileSaver singleCodeFileSaver = new SingleCodeFileSaver();
    private static final MultiCodeFileSaver multiFileSaver = new MultiCodeFileSaver();

    /**
     * 保存单文件代码
     *
     * @param codeResult
     * @param codeGenTypeEnum
     * @return
     */
    public static File executeSaver(Object codeResult, CodeGenTypeEnum codeGenTypeEnum) {
        return switch (codeGenTypeEnum) {
            case SINGLE_FILE -> singleCodeFileSaver.saveCode((SingleCodeResult) codeResult);
            case MULTI_FILE -> multiFileSaver.saveCode((MultiFileCodeResult) codeResult);
            default -> throw new BusinessException(ErrorCode.SYSTEM_ERROR, "不支持的代码生成类型");
        };
    }

    /**
     * 保存流式返回的代码
     *
     * @param codeStream      代码流
     * @param codeGenTypeEnum 生成类型
     * @return 原始流，以便 Facade 继续向前端推送
     */
    public static Flux<String> executeSaver(Flux<String> codeStream, CodeGenTypeEnum codeGenTypeEnum) {
        // 字符串拼接器,用于当流式返回所有的代码之后,再保存代码
        StringBuilder codeBuilder = new StringBuilder();
        return codeStream.doOnNext(codeBuilder::append)
                .doOnComplete(() -> {
                    try {
                        // 当所有代码都接收完毕后，解析并保存文件
                        String fullCode = codeBuilder.toString();
                        // 解析代码
                        Object parseResult = CodeParserExcutor.excutePaser(fullCode, codeGenTypeEnum);
                        // 保存代码
                        File saveDir = executeSaver(parseResult, codeGenTypeEnum);
                        log.info("保存成功,路径:{}", saveDir.getAbsolutePath());
                    } catch (Exception e) {
                        log.error("文件保存失败,原因:{}", e.getMessage(), e);
                    }
                });
    }
}
