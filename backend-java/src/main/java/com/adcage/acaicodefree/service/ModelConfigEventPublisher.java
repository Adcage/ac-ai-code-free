package com.adcage.acaicodefree.service;

import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class ModelConfigEventPublisher {

    private static final String CHANNEL_NAME = "model-config-events";

    @Resource
    private StringRedisTemplate stringRedisTemplate;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public void publishConfigUpdated(ModelConfig modelConfig) {
        try {
            Map<String, Object> event = new HashMap<>();
            event.put("eventType", "MODEL_CONFIG_UPDATED");
            event.put("modelConfigId", modelConfig.getId());
            event.put("configVersion", modelConfig.getConfigVersion());
            event.put("userId", modelConfig.getUserId());

            String message = objectMapper.writeValueAsString(event);
            stringRedisTemplate.convertAndSend(CHANNEL_NAME, message);
            log.info("发布模型配置更新事件: modelConfigId={}, configVersion={}", modelConfig.getId(), modelConfig.getConfigVersion());
        } catch (Exception e) {
            log.error("发布模型配置更新事件失败: {}", e.getMessage(), e);
        }
    }
}
