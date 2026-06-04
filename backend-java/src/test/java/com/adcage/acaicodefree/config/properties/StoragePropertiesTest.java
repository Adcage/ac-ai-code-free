package com.adcage.acaicodefree.config.properties;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StoragePropertiesTest {

    @Test
    void localUrlPrefixDefault_shouldContainApiContextPath() {
        StorageProperties.LocalConfig localConfig = new StorageProperties.LocalConfig();

        assertEquals("http://localhost:8700/api/storage", ReflectionTestUtils.getField(localConfig, "urlPrefix"));
    }

    @Test
    void localProfileUrlPrefix_shouldContainApiContextPath() throws Exception {
        ClassPathResource resource = new ClassPathResource("application-local.yml");
        String content = new String(resource.getInputStream().readAllBytes(), StandardCharsets.UTF_8);

        assertTrue(content.contains("url-prefix: http://localhost:8700/api/storage"));
    }
}
