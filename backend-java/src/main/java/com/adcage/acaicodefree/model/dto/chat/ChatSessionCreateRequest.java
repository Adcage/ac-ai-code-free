package com.adcage.acaicodefree.model.dto.chat;

import lombok.Data;

import java.io.Serializable;

/**
 * 创建会话请求
 */
@Data
public class ChatSessionCreateRequest implements Serializable {

    /**
     * 应用 id
     */
    private Long appId;

    private static final long serialVersionUID = 1L;
}
