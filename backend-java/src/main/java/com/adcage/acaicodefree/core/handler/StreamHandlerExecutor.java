package com.adcage.acaicodefree.core.handler;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class StreamHandlerExecutor {

    @Resource
    private SimpleTextStreamHandler simpleTextStreamHandler;

    @Resource
    private JsonMessageStreamHandler jsonMessageStreamHandler;

    public Flux<String> handle(CodeGenTypeEnum codeGenType, Flux<String> stream, StringBuilder readableOutput) {
        if (codeGenType == CodeGenTypeEnum.VUE_PROJECT
                || codeGenType == CodeGenTypeEnum.MULTI_FILE
                || codeGenType == CodeGenTypeEnum.SINGLE_FILE) {
            return jsonMessageStreamHandler.handle(stream, readableOutput);
        }
        return simpleTextStreamHandler.handle(stream, readableOutput);
    }
}
