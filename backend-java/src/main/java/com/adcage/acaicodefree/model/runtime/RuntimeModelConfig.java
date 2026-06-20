package com.adcage.acaicodefree.model.runtime;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeModelConfig {
    private String role;
    private Long modelConfigId;
    private Integer configVersion;
    private String provider;
    private String modelName;
    private String baseUrl;
    private String apiKey;
    private String source;
    private String billingMode;
}
