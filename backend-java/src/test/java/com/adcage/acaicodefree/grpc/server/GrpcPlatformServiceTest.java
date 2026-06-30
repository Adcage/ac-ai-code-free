package com.adcage.acaicodefree.grpc.server;

import com.adcage.acaicodefree.grpc.platform.CompleteAgentRunRequest;
import com.adcage.acaicodefree.grpc.platform.CompleteAgentRunResponse;
import com.adcage.acaicodefree.mapper.ChatHistoryMapper;
import com.adcage.acaicodefree.model.entity.AgentRun;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.ChatHistory;
import com.adcage.acaicodefree.service.AgentRunService;
import com.adcage.acaicodefree.service.AppService;
import com.adcage.acaicodefree.service.AppVersionService;
import com.adcage.acaicodefree.service.ScreenshotService;
import com.adcage.acaicodefree.service.UserService;
import com.adcage.acaicodefree.config.properties.RuntimeModelProperties;
import com.adcage.acaicodefree.core.build.VueProjectBuildService;
import io.grpc.stub.StreamObserver;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GrpcPlatformServiceTest {

    @Test
    void completeAgentRun_blankAiExtra_shouldPersistNullExtraAndNotFail() {
        GrpcPlatformService service = new GrpcPlatformService();
        AgentRunService agentRunService = mock(AgentRunService.class);
        AppVersionService appVersionService = mock(AppVersionService.class);
        AppService appService = mock(AppService.class);
        UserService userService = mock(UserService.class);
        VueProjectBuildService vueProjectBuildService = mock(VueProjectBuildService.class);
        ChatHistoryMapper chatHistoryMapper = mock(ChatHistoryMapper.class);
        ScreenshotService screenshotService = mock(ScreenshotService.class);
        RuntimeModelProperties runtimeModelProperties = new RuntimeModelProperties();

        ReflectionTestUtils.setField(service, "agentRunService", agentRunService);
        ReflectionTestUtils.setField(service, "appVersionService", appVersionService);
        ReflectionTestUtils.setField(service, "appService", appService);
        ReflectionTestUtils.setField(service, "userService", userService);
        ReflectionTestUtils.setField(service, "vueProjectBuildService", vueProjectBuildService);
        ReflectionTestUtils.setField(service, "chatHistoryMapper", chatHistoryMapper);
        ReflectionTestUtils.setField(service, "screenshotService", screenshotService);
        ReflectionTestUtils.setField(service, "runtimeModelProperties", runtimeModelProperties);

        long agentRunId = 1001L;
        long sessionId = 2002L;
        long appId = 3003L;
        long userId = 4004L;

        when(chatHistoryMapper.selectOneByQuery(any())).thenReturn(ChatHistory.builder().seqNo(1).build());
        when(agentRunService.getById(agentRunId)).thenReturn(AgentRun.builder()
                .id(agentRunId)
                .sessionId(sessionId)
                .appId(appId)
                .userId(userId)
                .build());
        when(appService.getById(appId)).thenReturn(App.builder().id(appId).codeGenType("single_file").build());

        @SuppressWarnings("unchecked")
        StreamObserver<CompleteAgentRunResponse> responseObserver = mock(StreamObserver.class);

        CompleteAgentRunRequest request = CompleteAgentRunRequest.newBuilder()
                .setAgentRunId(agentRunId)
                .setSuccess(true)
                .setWorkspacePath("C:/tmp/workspace")
                .setLatencyMs(123)
                .setAiMessage("好的，我已经了解了您的需求。")
                .setAiStatus("success")
                .setAiExtra("")
                .build();

        service.completeAgentRun(request, responseObserver);

        ArgumentCaptor<ChatHistory> captor = ArgumentCaptor.forClass(ChatHistory.class);
        verify(chatHistoryMapper).insert(captor.capture());
        assertNull(captor.getValue().getExtra(), "空 aiExtra 不应以空字符串写入 JSON 列");
        verify(responseObserver).onNext(any(CompleteAgentRunResponse.class));
        verify(responseObserver).onCompleted();
        verify(screenshotService).triggerCoverGenerationIfNeeded(eq(appId), eq(agentRunId));
    }

    @Test
    void completeAgentRun_validAiExtra_shouldPersistJsonUnchanged() {
        GrpcPlatformService service = new GrpcPlatformService();
        AgentRunService agentRunService = mock(AgentRunService.class);
        AppVersionService appVersionService = mock(AppVersionService.class);
        AppService appService = mock(AppService.class);
        UserService userService = mock(UserService.class);
        VueProjectBuildService vueProjectBuildService = mock(VueProjectBuildService.class);
        ChatHistoryMapper chatHistoryMapper = mock(ChatHistoryMapper.class);
        ScreenshotService screenshotService = mock(ScreenshotService.class);
        RuntimeModelProperties runtimeModelProperties = new RuntimeModelProperties();

        ReflectionTestUtils.setField(service, "agentRunService", agentRunService);
        ReflectionTestUtils.setField(service, "appVersionService", appVersionService);
        ReflectionTestUtils.setField(service, "appService", appService);
        ReflectionTestUtils.setField(service, "userService", userService);
        ReflectionTestUtils.setField(service, "vueProjectBuildService", vueProjectBuildService);
        ReflectionTestUtils.setField(service, "chatHistoryMapper", chatHistoryMapper);
        ReflectionTestUtils.setField(service, "screenshotService", screenshotService);
        ReflectionTestUtils.setField(service, "runtimeModelProperties", runtimeModelProperties);

        long agentRunId = 1101L;
        long sessionId = 2202L;
        long appId = 3303L;
        long userId = 4404L;
        String aiExtra = "{\"toolCalls\":[{\"type\":\"request\",\"name\":\"delegate_to_agent\"}]}";

        when(chatHistoryMapper.selectOneByQuery(any())).thenReturn(ChatHistory.builder().seqNo(2).build());
        when(agentRunService.getById(agentRunId)).thenReturn(AgentRun.builder()
                .id(agentRunId)
                .sessionId(sessionId)
                .appId(appId)
                .userId(userId)
                .build());
        when(appService.getById(appId)).thenReturn(App.builder().id(appId).codeGenType("single_file").build());

        @SuppressWarnings("unchecked")
        StreamObserver<CompleteAgentRunResponse> responseObserver = mock(StreamObserver.class);

        CompleteAgentRunRequest request = CompleteAgentRunRequest.newBuilder()
                .setAgentRunId(agentRunId)
                .setSuccess(true)
                .setWorkspacePath("C:/tmp/workspace")
                .setLatencyMs(88)
                .setAiMessage("任务已完成")
                .setAiStatus("success")
                .setAiExtra(aiExtra)
                .build();

        service.completeAgentRun(request, responseObserver);

        ArgumentCaptor<ChatHistory> captor = ArgumentCaptor.forClass(ChatHistory.class);
        verify(chatHistoryMapper).insert(captor.capture());
        assertEquals(aiExtra, captor.getValue().getExtra(), "合法 aiExtra 应原样写入 chat_history.extra");
    }
}
