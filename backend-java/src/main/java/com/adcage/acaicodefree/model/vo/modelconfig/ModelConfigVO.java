package com.adcage.acaicodefree.model.vo.modelconfig;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
public class ModelConfigVO implements Serializable {

    private Long id;

    private Long userId;

    private String provider;

    private String modelName;

    private String baseUrl;

    private Double temperature;

    private Integer maxTokens;

    private Integer configVersion;

    private Integer enabled;

    private Integer isDefault;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;

    private static final long serialVersionUID = 1L;
}
