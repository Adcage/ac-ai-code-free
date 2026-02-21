package com.adcage.acaicodefree.controller;

import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.common.BaseResponse;
import com.adcage.acaicodefree.common.DeleteRequest;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.exception.GlobalExceptionHandler;
import com.adcage.acaicodefree.model.dto.app.AppAddRequest;
import com.adcage.acaicodefree.model.dto.app.AppAdminUpdateRequest;
import com.adcage.acaicodefree.model.dto.app.AppEditRequest;
import com.adcage.acaicodefree.model.dto.app.AppQueryRequest;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.model.vo.app.AppVO;
import com.adcage.acaicodefree.service.AppService;
import com.adcage.acaicodefree.service.UserService;
import com.mybatisflex.core.paginate.Page;
import com.mybatisflex.core.query.QueryWrapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.ArrayList;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
class AppControllerTest {

    private MockMvc mockMvc;

    @Mock
    private AppService appService;

    @Mock
    private UserService userService;

    @InjectMocks
    private AppController appController;

    private User loginUser;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(appController)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
        loginUser = new User();
        loginUser.setId(1L);
        loginUser.setUserRole("user");
    }

    @Test
    void addApp_Success() throws Exception {
        AppAddRequest appAddRequest = new AppAddRequest();
        appAddRequest.setInitPrompt("Test Prompt for App Creation");

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(appService.save(any(App.class))).thenReturn(true);

        // ResultUtils.success returns code 0
        mockMvc.perform(post("/app/add")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appAddRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    void addApp_Fail_EmptyPrompt() throws Exception {
        AppAddRequest appAddRequest = new AppAddRequest();
        appAddRequest.setInitPrompt("");

        mockMvc.perform(post("/app/add")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appAddRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()));
    }

    @Test
    void deleteApp_Success() throws Exception {
        DeleteRequest deleteRequest = new DeleteRequest();
        deleteRequest.setId(1L);

        App app = new App();
        app.setId(1L);
        app.setUserId(loginUser.getId());

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(appService.getById(1L)).thenReturn(app);
        when(appService.removeById(1L)).thenReturn(true);

        mockMvc.perform(post("/app/delete")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(deleteRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").value(true));
    }

    @Test
    void deleteApp_Fail_NotOwner() throws Exception {
        DeleteRequest deleteRequest = new DeleteRequest();
        deleteRequest.setId(1L);

        App app = new App();
        app.setId(1L);
        app.setUserId(2L); // Different user

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(appService.getById(1L)).thenReturn(app);

        mockMvc.perform(post("/app/delete")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(deleteRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.NO_AUTH_ERROR.getCode()));
    }

    @Test
    void editApp_Success() throws Exception {
        AppEditRequest appEditRequest = new AppEditRequest();
        appEditRequest.setId(1L);
        appEditRequest.setAppName("Updated App Name");

        App app = new App();
        app.setId(1L);
        app.setUserId(loginUser.getId());

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(appService.getById(1L)).thenReturn(app);
        when(appService.updateById(any(App.class))).thenReturn(true);

        mockMvc.perform(post("/app/edit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appEditRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").value(true));
    }

    @Test
    void editApp_Fail_NotOwner() throws Exception {
        AppEditRequest appEditRequest = new AppEditRequest();
        appEditRequest.setId(1L);
        appEditRequest.setAppName("Updated App Name");

        App app = new App();
        app.setId(1L);
        app.setUserId(2L); // Different user

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(appService.getById(1L)).thenReturn(app);

        mockMvc.perform(post("/app/edit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appEditRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.NO_AUTH_ERROR.getCode()));
    }

    @Test
    void getAppVOById_Success() throws Exception {
        App app = new App();
        app.setId(1L);
        AppVO appVO = new AppVO();
        appVO.setId(1L);

        when(appService.getById(1L)).thenReturn(app);
        when(appService.getAppVO(app)).thenReturn(appVO);

        mockMvc.perform(get("/app/get/vo")
                        .param("id", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value(1L));
    }

    @Test
    void listMyAppVOByPage_Success() throws Exception {
        AppQueryRequest appQueryRequest = new AppQueryRequest();
        appQueryRequest.setPageNum(1);
        appQueryRequest.setPageSize(10);

        when(userService.getLoginUser(any())).thenReturn(loginUser);
        
        Page<App> appPage = new Page<>();
        appPage.setRecords(new ArrayList<>());
        appPage.setTotalRow(0);

        when(appService.page(any(Page.class), any(QueryWrapper.class))).thenReturn(appPage);
        when(appService.getQueryWrapper(any(AppQueryRequest.class))).thenReturn(new QueryWrapper());
        when(appService.getAppVOList(any())).thenReturn(new ArrayList<>());

        mockMvc.perform(post("/app/my/list/page/vo")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appQueryRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    void listGoodAppVOByPage_Success() throws Exception {
        AppQueryRequest appQueryRequest = new AppQueryRequest();
        appQueryRequest.setPageNum(1);
        appQueryRequest.setPageSize(10);

        Page<App> appPage = new Page<>();
        appPage.setRecords(new ArrayList<>());
        appPage.setTotalRow(0);

        when(appService.page(any(Page.class), any(QueryWrapper.class))).thenReturn(appPage);
        when(appService.getQueryWrapper(any(AppQueryRequest.class))).thenReturn(new QueryWrapper());
        when(appService.getAppVOList(any())).thenReturn(new ArrayList<>());

        mockMvc.perform(post("/app/good/list/page/vo")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appQueryRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    void updateApp_Success() throws Exception {
        AppAdminUpdateRequest appUpdateRequest = new AppAdminUpdateRequest();
        appUpdateRequest.setId(1L);
        appUpdateRequest.setAppName("Updated App Name Admin");

        App app = new App();
        app.setId(1L);

        // Mock admin user
        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        when(appService.updateById(any(App.class))).thenReturn(true);

        mockMvc.perform(post("/app/update")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appUpdateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").value(true));
    }

    @Test
    void deleteAppByAdmin_Success() throws Exception {
        DeleteRequest deleteRequest = new DeleteRequest();
        deleteRequest.setId(1L);

        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        when(appService.removeById(1L)).thenReturn(true);

        mockMvc.perform(post("/app/delete/admin")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(deleteRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").value(true));
    }

    @Test
    void getAppById_Success() throws Exception {
        App app = new App();
        app.setId(1L);

        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        when(appService.getById(1L)).thenReturn(app);

        mockMvc.perform(get("/app/get")
                        .param("id", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value(1L));
    }

    @Test
    void getAppVOByIdByAdmin_Success() throws Exception {
        App app = new App();
        app.setId(1L);
        AppVO appVO = new AppVO();
        appVO.setId(1L);

        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        when(appService.getById(1L)).thenReturn(app);
        when(appService.getAppVO(app)).thenReturn(appVO);

        mockMvc.perform(get("/app/admin/get/vo")
                        .param("id", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value(1L));
    }

    @Test
    void listAppVOByPageByAdmin_Success() throws Exception {
        AppQueryRequest appQueryRequest = new AppQueryRequest();
        appQueryRequest.setPageNum(1);
        appQueryRequest.setPageSize(10);

        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        Page<App> appPage = new Page<>();
        appPage.setRecords(new ArrayList<>());
        appPage.setTotalRow(0);

        when(appService.page(any(Page.class), any(QueryWrapper.class))).thenReturn(appPage);
        when(appService.getQueryWrapper(any(AppQueryRequest.class))).thenReturn(new QueryWrapper());
        when(appService.getAppVOList(any())).thenReturn(new ArrayList<>());

        mockMvc.perform(post("/app/admin/list/page/vo")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appQueryRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    void listAppByPage_Success() throws Exception {
        AppQueryRequest appQueryRequest = new AppQueryRequest();
        appQueryRequest.setPageNum(1);
        appQueryRequest.setPageSize(10);

        User adminUser = new User();
        adminUser.setId(1L);
        adminUser.setUserRole("admin");
        when(userService.getLoginUser(any())).thenReturn(adminUser);

        Page<App> appPage = new Page<>();
        appPage.setRecords(new ArrayList<>());
        appPage.setTotalRow(0);

        when(appService.page(any(Page.class), any(QueryWrapper.class))).thenReturn(appPage);
        when(appService.getQueryWrapper(any(AppQueryRequest.class))).thenReturn(new QueryWrapper());

        mockMvc.perform(post("/app/list/page")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(JSONUtil.toJsonStr(appQueryRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }
}
