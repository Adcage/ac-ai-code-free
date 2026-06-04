package com.adcage.acaicodefree.core.handler;

import cn.hutool.core.util.StrUtil;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class SimpleTextStreamHandler {

    public Flux<String> handle(Flux<String> stream, StringBuilder readableOutput) {
        return stream.doOnNext(chunk -> readableOutput.append(StrUtil.nullToEmpty(chunk)));
    }
}
