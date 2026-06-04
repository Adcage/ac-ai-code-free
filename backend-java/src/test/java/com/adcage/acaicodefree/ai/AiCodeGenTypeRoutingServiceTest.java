package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.service.impl.AppServiceImpl;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.test.util.ReflectionTestUtils;

class AiCodeGenTypeRoutingServiceTest {

    @Test
    void resolveCodeGenType_shouldUseExplicitValueFirst() {
        AppServiceImpl appService = new AppServiceImpl();
        Object result = ReflectionTestUtils.invokeMethod(appService,
                "resolveCodeGenType", "vue_project", "后台管理系统");
        Assertions.assertEquals(CodeGenTypeEnum.VUE_PROJECT, result);
    }

    @Test
    void resolveCodeGenType_shouldUseAiRoutingWhenNoExplicitValue() {
        AppServiceImpl appService = new AppServiceImpl();
        AiCodeGenTypeRoutingServiceFactory factory = Mockito.mock(AiCodeGenTypeRoutingServiceFactory.class);
        AiCodeGenTypeRoutingService routingService = Mockito.mock(AiCodeGenTypeRoutingService.class);
        Mockito.when(factory.createService()).thenReturn(routingService);
        Mockito.when(routingService.routeCodeGenType(Mockito.anyString())).thenReturn(CodeGenTypeEnum.SINGLE_FILE);
        ReflectionTestUtils.setField(appService, "aiCodeGenTypeRoutingServiceFactory", factory);

        Object result = ReflectionTestUtils.invokeMethod(appService,
                "resolveCodeGenType", null, "个人简介页面");
        Assertions.assertEquals(CodeGenTypeEnum.SINGLE_FILE, result);
    }

    @Test
    void resolveCodeGenType_shouldFallbackWhenAiThrowsException() {
        AppServiceImpl appService = new AppServiceImpl();
        AiCodeGenTypeRoutingServiceFactory factory = Mockito.mock(AiCodeGenTypeRoutingServiceFactory.class);
        Mockito.when(factory.createService()).thenThrow(new RuntimeException("ai unavailable"));
        ReflectionTestUtils.setField(appService, "aiCodeGenTypeRoutingServiceFactory", factory);

        Object result = ReflectionTestUtils.invokeMethod(appService,
                "resolveCodeGenType", null, "企业官网");
        Assertions.assertEquals(CodeGenTypeEnum.MULTI_FILE, result);
    }
}
