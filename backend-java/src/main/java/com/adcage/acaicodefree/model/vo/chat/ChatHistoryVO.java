package com.adcage.acaicodefree.model.vo.chat;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 聊天消息视图
 */
@Data
public class ChatHistoryVO implements Serializable {

    private Long id;

    private Long sessionId;

    private Integer seqNo;

    private String message;

    private String messageType;

    private String status;

    private Long appId;

    private Long userId;

    private String modelName;

    private Integer inputTokens;

    private Integer outputTokens;

    private Integer latencyMs;

    private String requestId;

    private String extra;

    private List<ToolEventVO> toolEvents;

    private LocalDateTime createTime;

    private static final long serialVersionUID = 1L;
}
