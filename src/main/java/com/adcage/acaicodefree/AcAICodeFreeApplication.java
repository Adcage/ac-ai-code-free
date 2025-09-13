package com.adcage.acaicodefree;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.adcage.acaicodefree.mapper")
public class AcAICodeFreeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AcAICodeFreeApplication.class, args);
    }

}
