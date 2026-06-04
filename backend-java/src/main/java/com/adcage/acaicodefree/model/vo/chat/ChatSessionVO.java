package com.adcage.acaicodefree.model.vo.chat;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 会话视图
 */
@Data
public class ChatSessionVO implements Serializable {

    private Long id;

    private Long appId;

    private Long userId;

    private String title;

    private Integer messageCount;

    private String modelName;

    private LocalDateTime lastMessageTime;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;

    private static final long serialVersionUID = 1L;
}
