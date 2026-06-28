package com.adcage.acaicodefree.model.dto.chat;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 聊天附件信息 DTO
 */
@Data
public class ChatAttachmentInfo implements Serializable {

    /**
     * 附件唯一标识
     */
    private String id;

    /**
     * 原始文件名
     */
    private String fileName;

    /**
     * 文件大小（字节）
     */
    private Long fileSize;

    /**
     * MIME 类型
     */
    private String mimeType;

    /**
     * 存储类型："local" | "cos"
     */
    private String storageType;

    /**
     * 存储相对路径 key
     */
    private String storagePath;

    /**
     * 文件完整访问 URL
     */
    private String url;

    @Serial
    private static final long serialVersionUID = 1L;
}
