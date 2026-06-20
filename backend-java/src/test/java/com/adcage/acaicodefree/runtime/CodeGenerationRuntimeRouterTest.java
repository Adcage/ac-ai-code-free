package com.adcage.acaicodefree.runtime;

import com.adcage.acaicodefree.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Flux;

import java.util.List;

class CodeGenerationRuntimeRouterTest {

    private CodeGenerationRuntimeRouter router;

    @BeforeEach
    void setUp() {
        router = new CodeGenerationRuntimeRouter();
        ReflectionTestUtils.setField(router, "runtimes", List.of(new StubRuntime("java-agent"), new StubRuntime("python-agent")));
    }

    @Test
    void select_shouldReturnPythonAgentByDefault() {
        ReflectionTestUtils.setField(router, "runtimeName", "python-agent");

        CodeGenerationRuntime selected = router.select();

        Assertions.assertEquals("python-agent", selected.getName());
    }

    @Test
    void select_shouldReturnConfiguredPythonRuntime() {
        ReflectionTestUtils.setField(router, "runtimeName", "python-agent");

        CodeGenerationRuntime selected = router.select();

        Assertions.assertEquals("python-agent", selected.getName());
    }

    @Test
    void select_shouldRejectJavaAgentRuntime() {
        ReflectionTestUtils.setField(router, "runtimeName", "java-agent");

        BusinessException exception = Assertions.assertThrows(BusinessException.class, router::select);

        Assertions.assertTrue(exception.getMessage().contains("Java AI runtime 已禁用"));
    }

    @Test
    void select_shouldThrowWhenRuntimeMissing() {
        ReflectionTestUtils.setField(router, "runtimes", List.of(new StubRuntime("java-agent")));
        ReflectionTestUtils.setField(router, "runtimeName", "python-agent");

        BusinessException exception = Assertions.assertThrows(BusinessException.class, router::select);

        Assertions.assertTrue(exception.getMessage().contains("未找到代码生成运行时"));
    }

    private record StubRuntime(String name) implements CodeGenerationRuntime {
        @Override
        public String getName() {
            return name;
        }

        @Override
        public Flux<String> stream(CodeGenerationRequest request) {
            return Flux.just("ok");
        }
    }
}
