package com.adcage.acaicodefree.mapper;

import com.mybatisflex.core.BaseMapper;
import com.adcage.acaicodefree.model.entity.AgentRun;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

public interface AgentRunMapper extends BaseMapper<AgentRun> {

    @Select("SELECT * FROM agent_run " +
            "WHERE appId = #{appId} AND sessionId = #{sessionId} AND userId = #{userId} " +
            "AND status = 'waiting_for_user' AND isDelete = 0 " +
            "ORDER BY createTime DESC LIMIT 1 FOR UPDATE")
    AgentRun selectLatestWaitingForUpdate(
            @Param("appId") Long appId,
            @Param("sessionId") Long sessionId,
            @Param("userId") Long userId
    );

    @Select("SELECT DISTINCT appId FROM agent_run " +
            "WHERE createTime > DATE_SUB(NOW(), INTERVAL #{lookbackHours} HOUR) " +
            "AND status IN ('completed', 'failed') " +
            "AND isDelete = 0")
    List<Long> selectRecentActiveAppIds(@Param("lookbackHours") int lookbackHours);
}
