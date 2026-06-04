package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.model.dto.app.AppQueryRequest;
import com.adcage.acaicodefree.service.AppService;
import com.mybatisflex.core.query.QueryWrapper;
import jakarta.annotation.Resource;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
public class AppServiceImplTest {

    @Resource
    private AppService appService;

    @Test
    public void testGetQueryWrapper() {
        AppQueryRequest request = new AppQueryRequest(); // All fields null
        request.setUserId(125L);
        QueryWrapper wrapper = appService.getQueryWrapper(request);
        System.out.println("SQL: " + wrapper.toSQL());
    }
}
