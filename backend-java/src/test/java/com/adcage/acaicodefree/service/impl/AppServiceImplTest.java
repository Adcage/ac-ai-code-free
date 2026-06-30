package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.model.enums.UserRoleEnum;
import com.adcage.acaicodefree.service.AppService;
import com.adcage.acaicodefree.service.UserService;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import javax.annotation.Resource;

@SpringBootTest
class AppServiceImplTest {

    @Resource
    private AppService appService;

    @Resource
    private UserService userService;

    @Test
    void testGetAppById() {
        App app = appService.getById(1L);
        Assertions.assertNotNull(app, "App should exist");
    }

    @Test
    void testGetAppByIdNotFound() {
        App app = appService.getById(-1L);
        Assertions.assertNull(app, "App should not exist for invalid ID");
    }
}
