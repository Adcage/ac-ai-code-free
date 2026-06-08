package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.mapper.ModelConfigMapper;
import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.service.ModelConfigEventPublisher;
import com.mybatisflex.annotation.Column;
import com.mybatisflex.core.query.QueryWrapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

class ModelConfigServiceImplTest {

    @Mock
    private ModelConfigMapper modelConfigMapper;

    @Mock
    private ModelConfigEventPublisher modelConfigEventPublisher;

    private ModelConfigServiceImpl modelConfigService;

    private ModelConfig buildModelConfig(Long id, Long userId, int enabled, int isDefault, LocalDateTime updateTime) {
        return ModelConfig.builder()
                .id(id)
                .userId(userId)
                .provider("openai")
                .modelName("gpt-4")
                .baseUrl("https://api.openai.com/v1")
                .apiKeyCipher("sk-test-key")
                .temperature(0.7)
                .maxTokens(8192)
                .configVersion(1)
                .enabled(enabled)
                .isDefault(isDefault)
                .createTime(LocalDateTime.now())
                .updateTime(updateTime)
                .build();
    }

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        modelConfigService = new ModelConfigServiceImpl();
        ReflectionTestUtils.setField(modelConfigService, "mapper", modelConfigMapper);
        ReflectionTestUtils.setField(modelConfigService, "modelConfigEventPublisher", modelConfigEventPublisher);
    }

    @Test
    void getDefaultEnabledModelConfig_ReturnsDefaultEnabledConfig() {
        ModelConfig defaultConfig = buildModelConfig(1L, 100L, 1, 1, LocalDateTime.now());
        when(modelConfigMapper.selectOneByQuery(any(QueryWrapper.class))).thenReturn(defaultConfig);

        ModelConfig result = modelConfigService.getDefaultEnabledModelConfig(100L);

        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals(1, result.getIsDefault());
        assertEquals(1, result.getEnabled());
    }

    @Test
    void getDefaultEnabledModelConfig_FallsBackToLatestEnabledConfig() {
        ModelConfig latestConfig = buildModelConfig(2L, 100L, 1, 0, LocalDateTime.now());
        when(modelConfigMapper.selectOneByQuery(any(QueryWrapper.class)))
                .thenReturn(null)
                .thenReturn(latestConfig);

        ModelConfig result = modelConfigService.getDefaultEnabledModelConfig(100L);

        assertNotNull(result);
        assertEquals(2L, result.getId());
        assertEquals(0, result.getIsDefault());
        assertEquals(1, result.getEnabled());
    }

    @Test
    void getDefaultEnabledModelConfig_ReturnsNullWhenNoEnabledConfig() {
        when(modelConfigMapper.selectOneByQuery(any(QueryWrapper.class)))
                .thenReturn(null)
                .thenReturn(null);

        ModelConfig result = modelConfigService.getDefaultEnabledModelConfig(100L);

        assertNull(result);
    }

    @Test
    void modelConfigColumnMapping_ShouldMatchCamelCaseDatabaseColumns() throws Exception {
        Map<String, String> expectedColumns = Map.of(
                "userId", "userId",
                "modelName", "modelName",
                "baseUrl", "baseUrl",
                "apiKeyCipher", "apiKeyCipher",
                "maxTokens", "maxTokens",
                "configVersion", "configVersion",
                "isDefault", "isDefault",
                "createTime", "createTime"
        );

        for (Map.Entry<String, String> entry : expectedColumns.entrySet()) {
            Column column = ModelConfig.class.getDeclaredField(entry.getKey()).getAnnotation(Column.class);
            assertNotNull(column, entry.getKey() + " should declare @Column");
            assertEquals(entry.getValue(), column.value());
        }
    }
}
