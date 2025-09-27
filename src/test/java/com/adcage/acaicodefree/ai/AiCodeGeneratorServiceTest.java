package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.model.HtmlCodeResult;
import com.adcage.acaicodefree.ai.model.MutiFileCodeResult;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AiCodeGeneratorServiceTest {

    @Resource
    private AiCodeGeneratorService aiCodeGeneratorService;

    @Test
    void generateSingleFileCode() {
        String userMessage = "做一个个人博客界面,不超20行";
        HtmlCodeResult code = aiCodeGeneratorService.generateSingleFileCode(userMessage);
        System.out.println(code);
    }

    @Test
    void generateMultiFileCode() {
        String userMessage = "做一个个人博客界面,不超过50行";
        MutiFileCodeResult code = aiCodeGeneratorService.generateMultiFileCode(userMessage);
        System.out.println(code);
    }

}