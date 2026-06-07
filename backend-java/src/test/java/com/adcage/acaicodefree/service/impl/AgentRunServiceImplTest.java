package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.entity.AgentRun;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.Serializable;

import static org.junit.jupiter.api.Assertions.*;

class AgentRunServiceImplTest {

    private AgentRun capturedAgentRun;

    private AgentRunServiceImpl agentRunService;

    @BeforeEach
    void setUp() {
        capturedAgentRun = null;
        agentRunService = new AgentRunServiceImpl() {
            @Override
            public boolean save(AgentRun entity) {
                capturedAgentRun = entity;
                entity.setId(1L);
                return true;
            }

            @Override
            public AgentRun getById(Serializable id) {
                if (id.equals(999L)) return null;
                return AgentRun.builder().id((Long) id).build();
            }

            @Override
            public boolean updateById(AgentRun entity) {
                return true;
            }
        };
    }

    @Test
    void createAgentRun_WithNewParams_SavesAllFields() {
        Long id = agentRunService.createAgentRun(100L, 200L, 300L, "python",
                10L, 2, "/workspace/run-1");

        assertNotNull(id);
        assertNotNull(capturedAgentRun);
        assertEquals(100L, capturedAgentRun.getAppId());
        assertEquals(200L, capturedAgentRun.getSessionId());
        assertEquals(300L, capturedAgentRun.getUserId());
        assertEquals("python", capturedAgentRun.getRuntime());
        assertEquals(10L, capturedAgentRun.getModelConfigId());
        assertEquals(2, capturedAgentRun.getConfigVersion());
        assertEquals("/workspace/run-1", capturedAgentRun.getWorkspacePath());
        assertEquals("running", capturedAgentRun.getStatus());
    }

    @Test
    void createAgentRun_OldMethod_DelegatesWithNullParams() {
        Long id = agentRunService.createAgentRun(100L, 200L, 300L, "java");

        assertNotNull(id);
        assertNotNull(capturedAgentRun);
        assertEquals(100L, capturedAgentRun.getAppId());
        assertEquals("java", capturedAgentRun.getRuntime());
        assertNull(capturedAgentRun.getModelConfigId());
        assertNull(capturedAgentRun.getWorkspacePath());
        assertEquals("running", capturedAgentRun.getStatus());
    }

    @Test
    void createAgentRun_InvalidAppId_ThrowsException() {
        assertThrows(BusinessException.class,
                () -> agentRunService.createAgentRun(null, 200L, 300L, "python"));
        assertThrows(BusinessException.class,
                () -> agentRunService.createAgentRun(-1L, 200L, 300L, "python"));
    }

    @Test
    void updateAgentRunWorkspacePath_UpdatesPath() {
        agentRunService.updateAgentRunWorkspacePath(1L, "/workspace/run-1");
    }

    @Test
    void updateAgentRunWorkspacePath_NotFound_ThrowsException() {
        assertThrows(BusinessException.class,
                () -> agentRunService.updateAgentRunWorkspacePath(999L, "/path"));
    }
}
