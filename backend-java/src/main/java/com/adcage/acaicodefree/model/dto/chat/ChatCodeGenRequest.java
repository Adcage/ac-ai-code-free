package com.adcage.acaicodefree.model.dto.chat;

import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * 对话生成代码请求
 */
@Data
public class ChatCodeGenRequest implements Serializable {

    /**
     * 应用 ID
     */
    private Long appId;

    /**
     * 会话 ID（为空时自动创建）
     */
    private Long sessionId;

    /**
     * 传递给运行时的真实消息
     */
    private String message;

    /**
     * 展示给用户并落库的消息；为空时回退到 message
     */
    private String displayMessage;

    /**
     * 附件列表
     */
    private List<ChatAttachmentInfo> attachments;

    private static final long serialVersionUID = 1L;
}
