package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.entity.AgentRun;
import com.mybatisflex.annotation.Column;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.Serializable;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class AgentRunServiceImplTest {

    private AgentRun capturedAgentRun;
    private AgentRun capturedUpdate;

    private AgentRunServiceImpl agentRunService;

    @BeforeEach
    void setUp() {
        capturedAgentRun = null;
        capturedUpdate = null;
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
                capturedUpdate = entity;
                return true;
            }
        };
    }

    @Test
    void createAgentRun_SavesAllFields() {
        Long id = agentRunService.createAgentRun(100L, 200L, 300L, "python");

        assertNotNull(id);
        assertNotNull(capturedAgentRun);
        assertEquals(100L, capturedAgentRun.getAppId());
        assertEquals(200L, capturedAgentRun.getSessionId());
        assertEquals(300L, capturedAgentRun.getUserId());
        assertEquals("python", capturedAgentRun.getRuntime());
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

    @Test
    void completeAgentRun_ClearsCheckpoint() {
        agentRunService.completeAgentRun(1L, "/workspace", 10);

        assertNotNull(capturedUpdate);
        assertEquals("completed", capturedUpdate.getStatus());
        assertEquals("", capturedUpdate.getLoopStateJson());
    }

    @Test
    void failAgentRun_ClearsCheckpoint() {
        agentRunService.failAgentRun(1L, "failed");

        assertNotNull(capturedUpdate);
        assertEquals("failed", capturedUpdate.getStatus());
        assertEquals("", capturedUpdate.getLoopStateJson());
    }

    @Test
    void agentRunColumnMapping_ShouldMatchCamelCaseDatabaseColumns() throws NoSuchFieldException {
        Map<String, String> expectedColumns = Map.of(
                "appId", "appId",
                "sessionId", "sessionId",
                "userId", "userId",
                "workspacePath", "workspacePath",
                "errorMessage", "errorMessage",
                "latencyMs", "latencyMs"
        );

        for (Map.Entry<String, String> entry : expectedColumns.entrySet()) {
            Column column = AgentRun.class.getDeclaredField(entry.getKey()).getAnnotation(Column.class);
            assertNotNull(column, entry.getKey() + " 缺少 @Column 注解");
            assertEquals(entry.getValue(), column.value(), entry.getKey() + " 数据库列名映射错误");
        }
    }
}
