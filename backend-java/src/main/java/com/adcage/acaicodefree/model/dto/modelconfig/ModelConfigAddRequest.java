package com.adcage.acaicodefree.model.dto.modelconfig;

import lombok.Data;

import java.io.Serializable;

@Data
public class ModelConfigAddRequest implements Serializable {

    private String provider;

    private String modelName;

    private String baseUrl;

    private String apiKeyCipher;

    private Double temperature;

    private Integer maxTokens;

    private static final long serialVersionUID = 1L;
}
