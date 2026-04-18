package com.adcage.acaicodefree;

import jakarta.annotation.Resource;
import org.junit.jupiter.api.Test;
import org.springframework.core.env.Environment;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
class AcAICodeFreeApplicationTests {

    @Resource
    private Environment environment;

    @Test
    void contextLoads() {
        assertNotNull(environment.getProperty("app.ai.vue-project.base-url"));
        assertEquals("20", environment.getProperty("app.ai.vue-project.memory-window-size"));
    }

}
