package com.adcage.acaicodefree.model.dto.modelconfig;

import lombok.Data;

import java.io.Serializable;

@Data
public class ModelConfigEditRequest implements Serializable {

    private Long id;

    private String provider;

    private String modelName;

    private String baseUrl;

    private String apiKeyCipher;

    private Double temperature;

    private Integer maxTokens;

    private Integer enabled;

    private Integer isDefault;

    private static final long serialVersionUID = 1L;
}
