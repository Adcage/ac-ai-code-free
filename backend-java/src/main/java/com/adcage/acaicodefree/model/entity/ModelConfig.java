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
@Table("model_config")
public class ModelConfig implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Id(keyType = KeyType.Generator, value = KeyGenerators.snowFlakeId)
    private Long id;

    private Long userId;

    private String provider;

    private String modelName;

    private String baseUrl;

    private String apiKeyCipher;

    @Builder.Default
    private Double temperature = 0.7;

    @Builder.Default
    private Integer maxTokens = 8192;

    @Builder.Default
    private Integer configVersion = 1;

    @Builder.Default
    private Integer enabled = 1;

    @Builder.Default
    private Integer isDefault = 0;

    private LocalDateTime createTime;

    @Column(value = "updateTime", onUpdateValue = "now()")
    private LocalDateTime updateTime;

    @Column(value = "isDelete", isLogicDelete = true)
    private Integer isDelete;

}
