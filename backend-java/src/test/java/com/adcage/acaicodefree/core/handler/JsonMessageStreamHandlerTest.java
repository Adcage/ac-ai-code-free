package com.adcage.acaicodefree.core.handler;

import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.ai.model.message.AiResponseMessage;
import com.adcage.acaicodefree.ai.model.message.ToolExecutedMessage;
import com.adcage.acaicodefree.ai.model.message.ToolRequestMessage;
import com.adcage.acaicodefree.service.FileOperationService;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Flux;

import java.util.List;

class JsonMessageStreamHandlerTest {

    @Test
    void jsonMessageHandlerShouldAppendAiResponseText() {
        JsonMessageStreamHandler handler = createHandler();
        StringBuilder readable = new StringBuilder();

        List<String> output = handler.handle(Flux.just(
                JSONUtil.toJsonStr(new AiResponseMessage("你好")),
                JSONUtil.toJsonStr(new AiResponseMessage("世界"))
        ), readable).collectList().block();

        Assertions.assertEquals("你好世界", readable.toString());
        Assertions.assertNotNull(output);
        Assertions.assertEquals(2, output.size());
    }

    @Test
    void jsonMessageHandlerShouldShowToolRequestOnlyOncePerId() {
        JsonMessageStreamHandler handler = createHandler();
        StringBuilder readable = new StringBuilder();

        String repeatedRequest = JSONUtil.toJsonStr(new ToolRequestMessage("t1", "writeFile", "{}"));
        List<String> output = handler.handle(Flux.just(repeatedRequest, repeatedRequest), readable).collectList().block();

        Assertions.assertNotNull(output);
        Assertions.assertEquals(1, output.size());
    }

    @Test
    void jsonMessageHandlerShouldUseToolExecutedAsFinalTrustedFileEvent() {
        JsonMessageStreamHandler handler = createHandler();
        StringBuilder readable = new StringBuilder();

        List<String> output = handler.handle(Flux.just(
                JSONUtil.toJsonStr(new ToolRequestMessage("t1", "writeFile", "{\"relativeFilePath\":\"src/main.js\"}")),
                JSONUtil.toJsonStr(new ToolExecutedMessage("t1", "writeFile", "{\"relativeFilePath\":\"src/main.js\"}", "文件写入成功：src/main.js"))
        ), readable).collectList().block();

        Assertions.assertNotNull(output);
        Assertions.assertEquals(2, output.size());
        Assertions.assertTrue(readable.toString().contains("[工具完成] 已写入文件 src/main.js"));
    }

    private JsonMessageStreamHandler createHandler() {
        JsonMessageStreamHandler handler = new JsonMessageStreamHandler();
        FileOperationService fileOperationService = new FileOperationService();
        ReflectionTestUtils.setField(handler, "fileOperationService", fileOperationService);
        return handler;
    }
}
