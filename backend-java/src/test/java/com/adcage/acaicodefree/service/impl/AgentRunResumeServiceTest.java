package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.mapper.AgentRunMapper;
import com.adcage.acaicodefree.model.entity.AgentRun;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class AgentRunResumeServiceTest {

    private AgentRunMapper agentRunMapper;
    private AgentRunServiceImpl service;

    @BeforeEach
    void setUp() {
        agentRunMapper = mock(AgentRunMapper.class);
        service = spy(new AgentRunServiceImpl());
        ReflectionTestUtils.setField(service, "mapper", agentRunMapper);
    }

    @Test
    void claimLatestPausedRun_ShouldMarkExistingRunRunning() {
        AgentRun paused = AgentRun.builder()
                .id(88L)
                .appId(1L)
                .sessionId(10L)
                .userId(100L)
                .status("waiting_for_user")
                .loopStateJson("{\"status\":\"waiting_for_user\"}")
                .build();
        when(agentRunMapper.selectLatestWaitingForUpdate(1L, 10L, 100L)).thenReturn(paused);
        doReturn(true).when(service).updateById(any(AgentRun.class));

        AgentRun claimed = service.claimLatestPausedRun(1L, 10L, 100L);

        assertSame(paused, claimed);
        ArgumentCaptor<AgentRun> update = ArgumentCaptor.forClass(AgentRun.class);
        verify(service).updateById(update.capture());
        assertEquals(88L, update.getValue().getId());
        assertEquals("running", update.getValue().getStatus());
        assertNotNull(claimed.getLoopStateJson());
    }

    @Test
    void claimLatestPausedRun_WhenNoPausedRun_ShouldReturnNull() {
        when(agentRunMapper.selectLatestWaitingForUpdate(1L, 10L, 100L)).thenReturn(null);

        AgentRun claimed = service.claimLatestPausedRun(1L, 10L, 100L);

        assertNull(claimed);
        verify(service, never()).updateById(any(AgentRun.class));
    }
}
