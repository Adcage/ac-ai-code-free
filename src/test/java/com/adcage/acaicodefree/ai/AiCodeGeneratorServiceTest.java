package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.ai.model.HtmlCodeResult;
import com.adcage.acaicodefree.ai.model.MutiFileCodeResult;
import jakarta.annotation.Resource;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AiCodeGeneratorServiceTest {

    @Resource
    private AiCodeGeneratorService aiCodeGeneratorService;

    @Test
    void generateSingleFileCode() {
        HtmlCodeResult code = aiCodeGeneratorService.generateSingleFileCode("做一个个人博客界面,不超20行");
        System.out.println(code);
    }

    @Test
    void generateMultiFileCode() {
        MutiFileCodeResult code = aiCodeGeneratorService.generateMultiFileCode("做一个个人博客界面,不超过50行");
        System.out.println(code);
    }

}