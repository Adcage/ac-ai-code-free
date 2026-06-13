package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.grpc.codegen.CodeGenerationServiceGrpc;
import com.adcage.acaicodefree.grpc.codegen.EnhancePromptRequest;
import com.adcage.acaicodefree.grpc.codegen.EnhancePromptResponse;
import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.service.ModelConfigService;
import com.adcage.acaicodefree.service.PythonPromptEnhanceService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
@Slf4j
public class PythonPromptEnhanceServiceImpl implements PythonPromptEnhanceService {

    @Resource
    private ModelConfigService modelConfigService;

    @GrpcClient("python-agent")
    private CodeGenerationServiceGrpc.CodeGenerationServiceBlockingStub codeGenBlockingStub;

    @Value("${agent.grpc.prompt-enhance-deadline-seconds:30}")
    private int promptEnhanceDeadlineSeconds;

    @Override
    public String enhancePrompt(String prompt, Long userId) {
        ThrowUtils.throwIf(StrUtil.isBlank(prompt), ErrorCode.PARAMS_ERROR, "提示词不能为空");
        ThrowUtils.throwIf(userId == null || userId <= 0, ErrorCode.NOT_LOGIN_ERROR, "用户未登录");

        ModelConfig defaultConfig = modelConfigService.getDefaultEnabledModelConfig(userId);
        ThrowUtils.throwIf(defaultConfig == null, ErrorCode.OPERATION_ERROR, "未找到可用的模型配置，请先配置模型");

        EnhancePromptRequest grpcRequest = EnhancePromptRequest.newBuilder()
                .setPrompt(prompt)
                .setModelConfigId(defaultConfig.getId() == null ? 0L : defaultConfig.getId())
                .setConfigVersion(defaultConfig.getConfigVersion() == null ? 0 : defaultConfig.getConfigVersion())
                .build();

        try {
            EnhancePromptResponse response = codeGenBlockingStub
                    .withWaitForReady()
                    .withDeadlineAfter(promptEnhanceDeadlineSeconds, TimeUnit.SECONDS)
                    .enhancePrompt(grpcRequest);
            if (response.getSuccess() && StrUtil.isNotBlank(response.getEnhancedPrompt())) {
                return response.getEnhancedPrompt();
            }
            String errorMessage = StrUtil.blankToDefault(response.getErrorMessage(), "Python 未返回有效提示词增强结果");
            throw new BusinessException(ErrorCode.OPERATION_ERROR, errorMessage);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("gRPC enhancePrompt 调用失败, userId={}", userId, e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "提示词优化服务暂时不可用");
        }
    }
}
