package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.config.properties.WorkspaceProperties;
import com.adcage.acaicodefree.core.handler.StreamHandlerExecutor;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.mapper.ChatHistoryMapper;
import com.adcage.acaicodefree.mapper.ChatSessionMapper;
import com.adcage.acaicodefree.model.dto.app.AppAddRequest;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.AgentRun;
import com.adcage.acaicodefree.model.entity.ChatHistory;
import com.adcage.acaicodefree.model.entity.ChatSession;
import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.runtime.CodeGenerationRequest;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntime;
import com.adcage.acaicodefree.runtime.CodeGenerationRuntimeRouter;
import com.adcage.acaicodefree.service.AgentRunService;
import com.adcage.acaicodefree.service.ModelConfigService;
import com.adcage.acaicodefree.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Flux;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class AppServiceImplTest {

    private AppServiceImpl appService;

    private ModelConfigService modelConfigService;
    private AgentRunService agentRunService;
    private WorkspaceProperties workspaceProperties;
    private CodeGenerationRuntimeRouter codeGenerationRuntimeRouter;
    private CodeGenerationRuntime mockRuntime;
    private ChatSessionMapper chatSessionMapper;
    private ChatHistoryMapper chatHistoryMapper;
    private StreamHandlerExecutor streamHandlerExecutor;

    @BeforeEach
    void setUp() {
        appService = spy(new AppServiceImpl());

        modelConfigService = mock(ModelConfigService.class);
        agentRunService = mock(AgentRunService.class);
        workspaceProperties = new WorkspaceProperties();
        codeGenerationRuntimeRouter = mock(CodeGenerationRuntimeRouter.class);
        mockRuntime = mock(CodeGenerationRuntime.class);
        chatSessionMapper = mock(ChatSessionMapper.class);
        chatHistoryMapper = mock(ChatHistoryMapper.class);
        streamHandlerExecutor = mock(StreamHandlerExecutor.class);

        ReflectionTestUtils.setField(appService, "modelConfigService", modelConfigService);
        ReflectionTestUtils.setField(appService, "agentRunService", agentRunService);
        ReflectionTestUtils.setField(appService, "workspaceProperties", workspaceProperties);
        ReflectionTestUtils.setField(appService, "codeGenerationRuntimeRouter", codeGenerationRuntimeRouter);
        ReflectionTestUtils.setField(appService, "chatSessionMapper", chatSessionMapper);
        ReflectionTestUtils.setField(appService, "chatHistoryMapper", chatHistoryMapper);
        ReflectionTestUtils.setField(appService, "streamHandlerExecutor", streamHandlerExecutor);

        when(mockRuntime.getName()).thenReturn("python-agent");
        when(mockRuntime.stream(any())).thenReturn(Flux.empty());
        when(streamHandlerExecutor.handle(any(), any(), any())).thenAnswer(invocation -> invocation.getArgument(1));
        when(codeGenerationRuntimeRouter.select()).thenReturn(mockRuntime);
    }

    @Test
    void createApp_withoutCodeGenTypeShouldUseFallbackAndNotCallJavaAiRouting() {
        AppAddRequest request = new AppAddRequest();
        request.setInitPrompt("做一个登录界面");
        User loginUser = User.builder().id(100L).build();
        doAnswer(invocation -> {
            App app = invocation.getArgument(0);
            app.setId(1000L);
            return true;
        }).when(appService).save(any(App.class));

        Long appId = appService.createApp(request, loginUser);

        assertNotNull(appId);
        ArgumentCaptor<App> appCaptor = ArgumentCaptor.forClass(App.class);
        verify(appService).save(appCaptor.capture());
        assertEquals(CodeGenTypeEnum.SINGLE_FILE.getValue(), appCaptor.getValue().getCodeGenType());
    }

    @Test
    void chatToGenCode_shouldResolveModelConfigAndPassToRuntime() {
        Long appId = 1L;
        Long sessionId = 10L;
        Long userId = 100L;
        String message = "build app";
        User loginUser = User.builder().id(userId).build();

        App app = new App();
        app.setId(appId);
        app.setUserId(userId);
        app.setCodeGenType(CodeGenTypeEnum.VUE_PROJECT.getValue());

        ChatSession chatSession = new ChatSession();
        chatSession.setId(sessionId);
        chatSession.setAppId(appId);
        chatSession.setUserId(userId);

        ModelConfig modelConfig = ModelConfig.builder()
                .id(42L)
                .configVersion(3)
                .build();

        doReturn(app).when(appService).getById(appId);
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(chatHistoryMapper.selectCountByQuery(any())).thenReturn(0L);
        when(chatHistoryMapper.insert(any())).thenReturn(1);
        when(modelConfigService.getDefaultEnabledModelConfig(userId)).thenReturn(modelConfig);
        when(agentRunService.createAgentRun(eq(appId), eq(sessionId), eq(userId), eq("python-agent"),
                eq(42L), eq(3), isNull())).thenReturn(99L);

        workspaceProperties.setAgentWorkspaceDir("/data/agent-workspaces");

        appService.chatToGenCode(appId, sessionId, message, message, null, loginUser);

        verify(modelConfigService).getDefaultEnabledModelConfig(userId);

        verify(agentRunService).createAgentRun(appId, sessionId, userId, "python-agent",
                42L, 3, null);

        String expectedWorkspacePath = "/data/agent-workspaces/vue_project/1";
        verify(agentRunService).updateAgentRunWorkspacePath(99L, expectedWorkspacePath);

        ArgumentCaptor<CodeGenerationRequest> requestCaptor = ArgumentCaptor.forClass(CodeGenerationRequest.class);
        verify(mockRuntime).stream(requestCaptor.capture());
        CodeGenerationRequest capturedRequest = requestCaptor.getValue();

        assertEquals(42L, capturedRequest.getModelConfigId());
        assertEquals(3, capturedRequest.getConfigVersion());
        assertEquals(expectedWorkspacePath, capturedRequest.getWorkspacePath());
    }

    @Test
    void chatToGenCode_shouldHandleNullModelConfig() {
        Long appId = 1L;
        Long sessionId = 10L;
        Long userId = 100L;
        String message = "build app";
        User loginUser = User.builder().id(userId).build();

        App app = new App();
        app.setId(appId);
        app.setUserId(userId);
        app.setCodeGenType(CodeGenTypeEnum.MULTI_FILE.getValue());

        ChatSession chatSession = new ChatSession();
        chatSession.setId(sessionId);
        chatSession.setAppId(appId);
        chatSession.setUserId(userId);

        doReturn(app).when(appService).getById(appId);
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(chatHistoryMapper.selectCountByQuery(any())).thenReturn(0L);
        when(chatHistoryMapper.insert(any())).thenReturn(1);
        when(modelConfigService.getDefaultEnabledModelConfig(userId)).thenReturn(null);
        when(agentRunService.createAgentRun(eq(appId), eq(sessionId), eq(userId), eq("python-agent"),
                isNull(), isNull(), isNull())).thenReturn(50L);

        workspaceProperties.setAgentWorkspaceDir("/tmp/workspaces");

        appService.chatToGenCode(appId, sessionId, message, message, null, loginUser);

        verify(agentRunService).createAgentRun(appId, sessionId, userId, "python-agent",
                null, null, null);

        String expectedWorkspacePath = "/tmp/workspaces/multi-file/1";
        verify(agentRunService).updateAgentRunWorkspacePath(50L, expectedWorkspacePath);

        ArgumentCaptor<CodeGenerationRequest> requestCaptor = ArgumentCaptor.forClass(CodeGenerationRequest.class);
        verify(mockRuntime).stream(requestCaptor.capture());
        CodeGenerationRequest capturedRequest = requestCaptor.getValue();

        assertNull(capturedRequest.getModelConfigId());
        assertNull(capturedRequest.getConfigVersion());
        assertEquals(expectedWorkspacePath, capturedRequest.getWorkspacePath());
    }

    @Test
    void chatToGenCode_shouldResumePausedRunWithoutCreatingAnotherRun() {
        Long appId = 1L;
        Long sessionId = 10L;
        Long userId = 100L;
        User loginUser = User.builder().id(userId).build();
        App app = new App();
        app.setId(appId);
        app.setUserId(userId);
        app.setCodeGenType(CodeGenTypeEnum.VUE_PROJECT.getValue());
        ChatSession chatSession = new ChatSession();
        chatSession.setId(sessionId);
        chatSession.setAppId(appId);
        chatSession.setUserId(userId);
        AgentRun paused = AgentRun.builder()
                .id(88L)
                .appId(appId)
                .sessionId(sessionId)
                .userId(userId)
                .modelConfigId(42L)
                .configVersion(3)
                .workspacePath("/data/agent-workspaces/88/source")
                .loopStateJson("{\"status\":\"waiting_for_user\"}")
                .build();
        doReturn(app).when(appService).getById(appId);
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(chatHistoryMapper.selectCountByQuery(any())).thenReturn(0L);
        when(chatHistoryMapper.insert(any())).thenReturn(1);
        when(agentRunService.claimLatestPausedRun(appId, sessionId, userId)).thenReturn(paused);

        appService.chatToGenCode(appId, sessionId, "企业后台登录页面", "企业后台登录页面", null, loginUser);

        verify(agentRunService, never()).createAgentRun(
                anyLong(), anyLong(), anyLong(), anyString(), any(), any(), any());
        ArgumentCaptor<CodeGenerationRequest> request =
                ArgumentCaptor.forClass(CodeGenerationRequest.class);
        verify(mockRuntime).stream(request.capture());
        assertEquals(88L, request.getValue().getAgentRunId());
        assertEquals(paused.getLoopStateJson(), request.getValue().getLoopStateJson());
        assertEquals(42L, request.getValue().getModelConfigId());
    }

    @Test
    void chatToGenCode_shouldRejectWhenSessionAlreadyHasRunningRun() {
        Long appId = 1L;
        Long sessionId = 10L;
        Long userId = 100L;
        User loginUser = User.builder().id(userId).build();
        App app = new App();
        app.setId(appId);
        app.setUserId(userId);
        app.setCodeGenType(CodeGenTypeEnum.VUE_PROJECT.getValue());
        ChatSession chatSession = new ChatSession();
        chatSession.setId(sessionId);
        chatSession.setAppId(appId);
        chatSession.setUserId(userId);
        doReturn(app).when(appService).getById(appId);
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(agentRunService.claimLatestPausedRun(appId, sessionId, userId)).thenReturn(null);
        when(agentRunService.hasRunningRun(appId, sessionId, userId)).thenReturn(true);

        BusinessException error = assertThrows(
                BusinessException.class,
                () -> appService.chatToGenCode(appId, sessionId, "重复提交", "重复提交", null, loginUser));

        assertTrue(error.getMessage().contains("当前会话正在生成"));
        verify(agentRunService, never()).createAgentRun(
                anyLong(), anyLong(), anyLong(), anyString(), any(), any(), any());
        verify(mockRuntime, never()).stream(any());
        verify(chatHistoryMapper, never()).insert(any());
    }

    @Test
    void chatToGenCode_shouldPersistDisplayMessageButSendRawMessageToRuntime() {
        Long appId = 1L;
        Long sessionId = 10L;
        Long userId = 100L;
        String runtimeMessage = "[[PLANNING_RESUME]]{\"questionSetId\":\"qs1\",\"answers\":{\"q1\":\"no_adjust\"}}[[/PLANNING_RESUME]]";
        String displayMessage = "需求补充：\n[q1]: no_adjust\n\n请继续生成。";
        User loginUser = User.builder().id(userId).build();

        App app = new App();
        app.setId(appId);
        app.setUserId(userId);
        app.setCodeGenType(CodeGenTypeEnum.VUE_PROJECT.getValue());

        ChatSession chatSession = new ChatSession();
        chatSession.setId(sessionId);
        chatSession.setAppId(appId);
        chatSession.setUserId(userId);

        doReturn(app).when(appService).getById(appId);
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(chatHistoryMapper.selectCountByQuery(any())).thenReturn(0L, 1L);
        when(chatHistoryMapper.insert(any())).thenReturn(1);
        when(modelConfigService.getDefaultEnabledModelConfig(userId)).thenReturn(null);
        when(agentRunService.createAgentRun(eq(appId), eq(sessionId), eq(userId), eq("python-agent"),
                isNull(), isNull(), isNull())).thenReturn(77L);

        appService.chatToGenCode(appId, sessionId, runtimeMessage, displayMessage, null, loginUser);

        ArgumentCaptor<ChatHistory> historyCaptor = ArgumentCaptor.forClass(ChatHistory.class);
        verify(chatHistoryMapper, atLeastOnce()).insert(historyCaptor.capture());
        assertEquals(displayMessage, historyCaptor.getAllValues().get(0).getMessage());

        ArgumentCaptor<CodeGenerationRequest> requestCaptor = ArgumentCaptor.forClass(CodeGenerationRequest.class);
        verify(mockRuntime).stream(requestCaptor.capture());
        assertEquals(runtimeMessage, requestCaptor.getValue().getMessage());
    }
}
