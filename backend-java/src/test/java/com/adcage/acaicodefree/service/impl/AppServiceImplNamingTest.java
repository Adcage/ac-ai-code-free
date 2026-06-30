package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.mapper.ChatSessionMapper;
import com.adcage.acaicodefree.model.dto.app.AppAddRequest;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.ChatSession;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.service.PythonTitleGenerationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AppServiceImplNamingTest {

    private AppServiceImpl service;
    private PythonTitleGenerationService titleGenerationService;
    private ChatSessionMapper chatSessionMapper;

    @BeforeEach
    void setUp() {
        service = spy(new AppServiceImpl());
        titleGenerationService = mock(PythonTitleGenerationService.class);
        chatSessionMapper = mock(ChatSessionMapper.class);
        ReflectionTestUtils.setField(service, "pythonTitleGenerationService", titleGenerationService);
        ReflectionTestUtils.setField(service, "chatSessionMapper", chatSessionMapper);
        doAnswer(invocation -> {
            App app = invocation.getArgument(0);
            app.setId(101L);
            return true;
        }).when(service).save(any(App.class));
    }

    @Test
    void createAppShouldUseGeneratedTitleWhenAvailable() {
        AppAddRequest request = new AppAddRequest();
        request.setInitPrompt("请帮我做一个智能排班系统，支持日历和冲突检测");
        request.setCodeGenType("multi-file");
        User loginUser = new User();
        loginUser.setId(1L);
        when(titleGenerationService.generateAppTitle(request.getInitPrompt(), 1L)).thenReturn("智能排班助手");

        service.createApp(request, loginUser);

        ArgumentCaptor<App> appCaptor = ArgumentCaptor.forClass(App.class);
        verify(service).save(appCaptor.capture());
        assertEquals("智能排班助手", appCaptor.getValue().getAppName());
    }

    @Test
    void createAppShouldFallbackWhenTitleGenerationFails() {
        AppAddRequest request = new AppAddRequest();
        request.setInitPrompt("请帮我做一个 CRM 销售看板，支持线索分配");
        request.setCodeGenType("multi-file");
        User loginUser = new User();
        loginUser.setId(1L);
        when(titleGenerationService.generateAppTitle(request.getInitPrompt(), 1L))
                .thenThrow(new RuntimeException("grpc down"));

        service.createApp(request, loginUser);

        ArgumentCaptor<App> appCaptor = ArgumentCaptor.forClass(App.class);
        verify(service).save(appCaptor.capture());
        assertEquals("CRM 销售看板", appCaptor.getValue().getAppName());
    }

    @Test
    void tryAutoRenameSessionTitleShouldRenameDefaultSession() {
        App app = App.builder()
                .appName("智能排班助手")
                .initPrompt("请帮我做一个智能排班系统")
                .build();
        ChatSession chatSession = ChatSession.builder()
                .id(9L)
                .title("新会话 1")
                .messageCount(1)
                .build();
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);
        when(titleGenerationService.generateSessionTitle("智能排班助手", "请帮我做一个智能排班系统", "请先做登录页", 1L))
                .thenReturn("登录页设计");

        ReflectionTestUtils.invokeMethod(service, "tryAutoRenameSessionTitle", 9L, app, "请先做登录页", 1L);

        ArgumentCaptor<ChatSession> sessionCaptor = ArgumentCaptor.forClass(ChatSession.class);
        verify(chatSessionMapper).update(sessionCaptor.capture());
        assertEquals("登录页设计", sessionCaptor.getValue().getTitle());
    }

    @Test
    void tryAutoRenameSessionTitleShouldSkipCustomTitle() {
        App app = App.builder()
                .appName("智能排班助手")
                .initPrompt("请帮我做一个智能排班系统")
                .build();
        ChatSession chatSession = ChatSession.builder()
                .id(9L)
                .title("排班规则讨论")
                .messageCount(1)
                .build();
        when(chatSessionMapper.selectOneByQuery(any())).thenReturn(chatSession);

        ReflectionTestUtils.invokeMethod(service, "tryAutoRenameSessionTitle", 9L, app, "请先做登录页", 1L);

        verify(titleGenerationService, never()).generateSessionTitle(any(), any(), any(), any());
        verify(chatSessionMapper, never()).update(any());
    }
}
