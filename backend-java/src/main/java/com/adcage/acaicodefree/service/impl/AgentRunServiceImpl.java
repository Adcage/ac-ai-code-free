package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.mapper.AgentRunMapper;
import com.adcage.acaicodefree.model.entity.AgentRun;
import com.adcage.acaicodefree.service.AgentRunService;
import com.mybatisflex.spring.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AgentRunServiceImpl extends ServiceImpl<AgentRunMapper, AgentRun> implements AgentRunService {

    @Override
    public Long createAgentRun(Long appId, Long sessionId, Long userId, String runtime) {
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        ThrowUtils.throwIf(sessionId == null || sessionId <= 0, ErrorCode.PARAMS_ERROR, "会话 ID 不能为空");
        ThrowUtils.throwIf(userId == null || userId <= 0, ErrorCode.PARAMS_ERROR, "用户 ID 不能为空");
        AgentRun agentRun = AgentRun.builder()
                .appId(appId)
                .sessionId(sessionId)
                .userId(userId)
                .runtime(runtime)
                .status("running")
                .latencyMs(0)
                .createTime(LocalDateTime.now())
                .build();
        boolean saveResult = this.save(agentRun);
        ThrowUtils.throwIf(!saveResult, ErrorCode.OPERATION_ERROR, "创建 AgentRun 失败");
        return agentRun.getId();
    }

    @Override
    public void completeAgentRun(Long id, String workspacePath, Integer latencyMs) {
        ThrowUtils.throwIf(id == null || id <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        AgentRun agentRun = this.getById(id);
        ThrowUtils.throwIf(agentRun == null, ErrorCode.NOT_FOUND_ERROR, "AgentRun 不存在");
        AgentRun update = AgentRun.builder()
                .id(id)
                .status("completed")
                .workspacePath(workspacePath)
                .latencyMs(latencyMs)
                .build();
        boolean result = this.updateById(update);
        ThrowUtils.throwIf(!result, ErrorCode.OPERATION_ERROR, "更新 AgentRun 状态失败");
    }

    @Override
    public void failAgentRun(Long id, String errorMessage) {
        ThrowUtils.throwIf(id == null || id <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        AgentRun agentRun = this.getById(id);
        ThrowUtils.throwIf(agentRun == null, ErrorCode.NOT_FOUND_ERROR, "AgentRun 不存在");
        AgentRun update = AgentRun.builder()
                .id(id)
                .status("failed")
                .errorMessage(errorMessage)
                .build();
        boolean result = this.updateById(update);
        ThrowUtils.throwIf(!result, ErrorCode.OPERATION_ERROR, "更新 AgentRun 状态失败");
    }
}
