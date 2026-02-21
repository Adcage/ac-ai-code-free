package com.adcage.acaicodefree.core;

import cn.hutool.core.util.IdUtil;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import reactor.core.publisher.Flux;

import java.io.File;
import java.util.List;

@Slf4j
@SpringBootTest
class AiCodeGeneratorFacadeTest {
    @Resource
    private AiCodeGeneratorFacade aiCodeGeneratorFacade;

    @Test
    void generateAndSaveCode() {
        long snowflakeNextId = IdUtil.getSnowflakeNextId();
        log.info("snowflakeNextId: {}", snowflakeNextId);
        File file = aiCodeGeneratorFacade.generateAndSaveCode("生成一个HTML网页,不超过100行", CodeGenTypeEnum.SINGLE_FILE, snowflakeNextId);
        Assertions.assertNotNull(file);
    }

    @Test
    public void generateAndSaveCodeStream() {
        long snowflakeNextId = IdUtil.getSnowflakeNextId();
        log.info("snowflakeNextId: {}", snowflakeNextId);
        Flux<String> stringFlux = aiCodeGeneratorFacade.generateAndSaveCodeStream("生成一个HTML登录网页", CodeGenTypeEnum.SINGLE_FILE, snowflakeNextId);
        List<String> result = stringFlux.collectList().block();

        Assertions.assertNotNull(result);

        String compileContent = String.join("", result);
        System.out.println(compileContent);

    }

    @Test
    public void generateAndSaveMultiCodeStream() {
        long snowflakeNextId = IdUtil.getSnowflakeNextId();
        log.info("snowflakeNextId: {}", snowflakeNextId);
        Flux<String> stringFlux = aiCodeGeneratorFacade.generateAndSaveCodeStream("生成一个HTML登录网页", CodeGenTypeEnum.MULTI_FILE, snowflakeNextId);
        List<String> result = stringFlux.collectList().block();

        Assertions.assertNotNull(result);

        String compileContent = String.join("", result);
        System.out.println(compileContent);

    }
}