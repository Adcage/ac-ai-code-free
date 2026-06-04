package com.adcage.acaicodefree.config.properties;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "cos.client")
@Data
public class CosClientProperties {

    private String host;

    private String secretId;

    private String secretKey;

    private String region;

    private String bucket;

}
