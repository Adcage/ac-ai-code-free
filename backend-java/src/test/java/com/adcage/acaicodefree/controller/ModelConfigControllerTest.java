package com.adcage.acaicodefree.controller;

import com.adcage.acaicodefree.exception.GlobalExceptionHandler;
import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.model.vo.modelconfig.ModelConfigVO;
import com.adcage.acaicodefree.service.ModelConfigService;
import com.adcage.acaicodefree.service.UserService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.lang.reflect.Field;
import java.time.LocalDateTime;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class ModelConfigControllerTest {

    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Mock
    private ModelConfigService modelConfigService;

    @Mock
    private UserService userService;

    @InjectMocks
    private ModelConfigController modelConfigController;

    private ModelConfig buildEnabledModelConfig() {
        return ModelConfig.builder()
                .id(1L)
                .userId(1L)
                .provider("openai")
                .modelName("gpt-4")
                .baseUrl("https://api.openai.com/v1")
                .apiKeyCipher("sk-test-secret-key-123")
                .temperature(0.7)
                .maxTokens(8192)
                .configVersion(1)
                .enabled(1)
                .isDefault(0)
                .createTime(LocalDateTime.now())
                .updateTime(LocalDateTime.now())
                .build();
    }

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(modelConfigController)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
        ReflectionTestUtils.setField(modelConfigController, "internalSecret", "test-internal-secret");
    }

    @Test
    void getRuntimeConfig_ReturnsApiKey_WhenSecretValid() throws Exception {
        ModelConfig config = buildEnabledModelConfig();
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "1")
                        .header("X-Internal-Secret", "test-internal-secret"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.apiKey").value("sk-test-secret-key-123"))
                .andExpect(jsonPath("$.data.provider").value("openai"))
                .andExpect(jsonPath("$.data.modelName").value("gpt-4"))
                .andExpect(jsonPath("$.data.baseUrl").value("https://api.openai.com/v1"));
    }

    @Test
    void getRuntimeConfig_RejectsRequestWithoutSecret() throws Exception {
        ModelConfig config = buildEnabledModelConfig();
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(40101));
    }

    @Test
    void getRuntimeConfig_RejectsRequestWithWrongSecret() throws Exception {
        ModelConfig config = buildEnabledModelConfig();
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "1")
                        .header("X-Internal-Secret", "wrong-secret"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(40101));
    }

    @Test
    void getRuntimeConfig_RejectsDisabledConfig() throws Exception {
        ModelConfig config = buildEnabledModelConfig();
        config.setEnabled(0);
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "1")
                        .header("X-Internal-Secret", "test-internal-secret"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(40000));
    }

    @Test
    void getRuntimeConfig_RejectsVersionMismatch() throws Exception {
        ModelConfig config = buildEnabledModelConfig();
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "2")
                        .header("X-Internal-Secret", "test-internal-secret"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(40000));
    }

    @Test
    void publicModelConfigVO_DoesNotExposeApiKey() {
        ModelConfigVO vo = new ModelConfigVO();
        vo.setId(1L);
        vo.setProvider("openai");
        vo.setModelName("gpt-4");
        vo.setBaseUrl("https://api.openai.com/v1");

        boolean hasApiKeyField = false;
        for (Field field : vo.getClass().getDeclaredFields()) {
            if (field.getName().toLowerCase().contains("apikey") || field.getName().toLowerCase().contains("apikeycipher")) {
                hasApiKeyField = true;
                break;
            }
        }
        assert !hasApiKeyField : "ModelConfigVO must not contain any API key field";
    }

    @Test
    void runtimeVO_ContainsApiKeyField() {
        ModelConfigController.ModelConfigRuntimeVO runtimeVO = new ModelConfigController.ModelConfigRuntimeVO();
        runtimeVO.setProvider("openai");
        runtimeVO.setModelName("gpt-4");
        runtimeVO.setBaseUrl("https://api.openai.com/v1");
        runtimeVO.setApiKey("sk-test-key");

        boolean hasApiKeyField = false;
        for (Field field : runtimeVO.getClass().getDeclaredFields()) {
            if (field.getName().equals("apiKey")) {
                hasApiKeyField = true;
                break;
            }
        }
        assert hasApiKeyField : "ModelConfigRuntimeVO must contain apiKey field";
        assert "sk-test-key".equals(runtimeVO.getApiKey()) : "apiKey getter must work";
    }

    @Test
    void getRuntimeConfig_AllowsRequestWhenNoSecretConfigured() throws Exception {
        ReflectionTestUtils.setField(modelConfigController, "internalSecret", "");
        ModelConfig config = buildEnabledModelConfig();
        when(modelConfigService.getById(1L)).thenReturn(config);

        mockMvc.perform(get("/model-config/internal/runtime")
                        .param("id", "1")
                        .param("configVersion", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.apiKey").value("sk-test-secret-key-123"));
    }
}
