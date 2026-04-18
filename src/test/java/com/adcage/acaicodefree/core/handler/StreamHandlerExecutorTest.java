package com.adcage.acaicodefree.core.handler;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Flux;

class StreamHandlerExecutorTest {

    @Test
    void simpleTextHandlerShouldAppendRawTextForLegacyModes() {
        StreamHandlerExecutor executor = createExecutor();
        StringBuilder readable = new StringBuilder();

        executor.handle(CodeGenTypeEnum.MULTI_FILE, Flux.just("a", "b"), readable).collectList().block();

        Assertions.assertEquals("ab", readable.toString());
    }

    @Test
    void shouldRouteVueProjectToJsonHandler() {
        StreamHandlerExecutor executor = createExecutor();
        StringBuilder readable = new StringBuilder();

        executor.handle(CodeGenTypeEnum.VUE_PROJECT, Flux.just("{\"type\":\"ai_response\",\"data\":\"ok\"}"), readable)
                .collectList()
                .block();

        Assertions.assertEquals("ok", readable.toString());
    }

    private StreamHandlerExecutor createExecutor() {
        StreamHandlerExecutor executor = new StreamHandlerExecutor();
        ReflectionTestUtils.setField(executor, "simpleTextStreamHandler", new SimpleTextStreamHandler());
        ReflectionTestUtils.setField(executor, "jsonMessageStreamHandler", new JsonMessageStreamHandler());
        return executor;
    }
}
