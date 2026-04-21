package com.adcage.acaicodefree.config;

import com.adcage.acaicodefree.config.properties.CosClientProperties;
import com.qcloud.cos.COSClient;
import com.qcloud.cos.auth.BasicCOSCredentials;
import com.qcloud.cos.auth.COSCredentials;
import com.qcloud.cos.region.Region;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConditionalOnProperty(prefix = "storage", name = "type", havingValue = "cos", matchIfMissing = true)
@EnableConfigurationProperties(CosClientProperties.class)
public class CosClientConfig {

    @Bean(destroyMethod = "shutdown")
    public COSClient cosClient(CosClientProperties cosClientProperties) {
        COSCredentials cosCredentials = new BasicCOSCredentials(cosClientProperties.getSecretId(),
                cosClientProperties.getSecretKey());
        com.qcloud.cos.ClientConfig clientConfig = new com.qcloud.cos.ClientConfig(
                new Region(cosClientProperties.getRegion()));
        return new COSClient(cosCredentials, clientConfig);
    }
}
