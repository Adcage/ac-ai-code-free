package com.adcage.acaicodefree.mapper;

import com.adcage.acaicodefree.model.entity.ChatSession;
import com.mybatisflex.core.BaseMapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 对话会话 映射层。
 */
public interface ChatSessionMapper extends BaseMapper<ChatSession> {

    @Select("SELECT * FROM chat_session WHERE id = #{sessionId} AND isDelete = 0 FOR UPDATE")
    ChatSession selectByIdForUpdate(@Param("sessionId") Long sessionId);
}
