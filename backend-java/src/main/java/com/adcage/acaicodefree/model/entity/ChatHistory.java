package com.adcage.acaicodefree.model.entity;

import com.mybatisflex.annotation.Column;
import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import com.mybatisflex.core.keygen.KeyGenerators;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 对话历史 实体类。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table("chat_history")
public class ChatHistory implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Id(keyType = KeyType.Generator, value = KeyGenerators.snowFlakeId)
    private Long id;

    @Column("sessionId")
    private Long sessionId;

    @Column("seqNo")
    private Integer seqNo;

    private String message;

    @Column("messageType")
    private String messageType;

    private String status;

    @Column("appId")
    private Long appId;

    @Column("userId")
    private Long userId;

    @Column("modelName")
    private String modelName;

    @Column("latencyMs")
    private Integer latencyMs;

    @Column("requestId")
    private String requestId;

    private String extra;

    @Column(value = "createTime", onInsertValue = "now()")
    private LocalDateTime createTime;

    @Column(value = "updateTime", onInsertValue = "now()", onUpdateValue = "now()")
    private LocalDateTime updateTime;

    @Column(value = "isDelete", isLogicDelete = true)
    private Integer isDelete;
}
