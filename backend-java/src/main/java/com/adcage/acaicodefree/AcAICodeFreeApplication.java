package com.adcage.acaicodefree;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@MapperScan("com.adcage.acaicodefree.mapper")
@EnableCaching
public class AcAICodeFreeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AcAICodeFreeApplication.class, args);
    }

}
