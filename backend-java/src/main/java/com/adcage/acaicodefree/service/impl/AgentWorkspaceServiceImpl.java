package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.WorkspaceProperties;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.service.AgentWorkspaceService;
import jakarta.annotation.Resource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class AgentWorkspaceServiceImpl implements AgentWorkspaceService {

    private static final Logger log = LoggerFactory.getLogger(AgentWorkspaceServiceImpl.class);

    @Resource
    private WorkspaceProperties workspaceProperties;

    @Override
    public Path initWorkspace(Long agentRunId, Long appId) {
        ThrowUtils.throwIf(agentRunId == null || agentRunId <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        Path sourceDir = getWorkspaceSourceDir(agentRunId);
        try {
            Files.createDirectories(sourceDir);
        } catch (IOException e) {
            log.error("创建工作空间目录失败, agentRunId={}", agentRunId, e);
            throw new RuntimeException("创建工作空间目录失败", e);
        }
        return sourceDir;
    }

    @Override
    public Path getWorkspaceSourceDir(Long agentRunId) {
        ThrowUtils.throwIf(agentRunId == null || agentRunId <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        return Path.of(workspaceProperties.getAgentWorkspaceDir())
                .resolve(String.valueOf(agentRunId))
                .resolve("source");
    }

    @Override
    public void cleanupWorkspace(Long agentRunId) {
        ThrowUtils.throwIf(agentRunId == null || agentRunId <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        Path workspaceDir = Path.of(workspaceProperties.getAgentWorkspaceDir())
                .resolve(String.valueOf(agentRunId));
        try {
            if (Files.exists(workspaceDir)) {
                Files.walk(workspaceDir)
                        .sorted((a, b) -> b.compareTo(a))
                        .forEach(path -> {
                            try {
                                Files.deleteIfExists(path);
                            } catch (IOException e) {
                                log.warn("删除工作空间文件失败, path={}", path, e);
                            }
                        });
            }
        } catch (IOException e) {
            log.error("清理工作空间失败, agentRunId={}", agentRunId, e);
        }
    }
}
