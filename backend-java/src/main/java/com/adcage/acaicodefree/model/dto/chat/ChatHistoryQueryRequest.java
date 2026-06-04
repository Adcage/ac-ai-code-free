package com.adcage.acaicodefree.model.dto.chat;

import com.adcage.acaicodefree.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 查询聊天历史请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class ChatHistoryQueryRequest extends PageRequest implements Serializable {

    /**
     * 应用 id
     */
    private Long appId;

    /**
     * 会话 id
     */
    private Long sessionId;

    private static final long serialVersionUID = 1L;
}
