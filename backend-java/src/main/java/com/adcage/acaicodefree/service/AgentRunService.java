package com.adcage.acaicodefree.service;

import com.mybatisflex.core.service.IService;
import com.adcage.acaicodefree.model.entity.AgentRun;

public interface AgentRunService extends IService<AgentRun> {

    Long createAgentRun(Long appId, Long sessionId, Long userId, String runtime);

    void completeAgentRun(Long id, String workspacePath, Integer latencyMs);

    void failAgentRun(Long id, String errorMessage);
}
