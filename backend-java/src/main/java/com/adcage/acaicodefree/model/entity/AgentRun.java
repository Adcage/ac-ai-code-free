package com.adcage.acaicodefree.model.entity;

import com.mybatisflex.annotation.Column;
import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import java.io.Serializable;
import java.time.LocalDateTime;

import java.io.Serial;

import com.mybatisflex.core.keygen.KeyGenerators;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table("agent_run")
public class AgentRun implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Id(keyType = KeyType.Generator, value = KeyGenerators.snowFlakeId)
    private Long id;

    @Column("appId")
    private Long appId;

    @Column("sessionId")
    private Long sessionId;

    @Column("userId")
    private Long userId;

    private String runtime;

    private String status;

    @Column("workspacePath")
    private String workspacePath;

    @Column("errorMessage")
    private String errorMessage;

    @Column("latencyMs")
    @Builder.Default
    private Integer latencyMs = 0;

    @Column("loopStateJson")
    private String loopStateJson;

    @Column("createTime")
    private LocalDateTime createTime;

    @Column(value = "updateTime", onUpdateValue = "now()")
    private LocalDateTime updateTime;

    @Column(value = "isDelete", isLogicDelete = true)
    private Integer isDelete;
}
