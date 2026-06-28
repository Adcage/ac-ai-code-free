package com.adcage.acaicodefree.controller;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.common.ResultUtils;
import com.adcage.acaicodefree.config.properties.StorageProperties;
import com.adcage.acaicodefree.exception.GlobalExceptionHandler;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.model.dto.chat.ChatAttachmentInfo;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.service.UserService;
import com.adcage.acaicodefree.storage.FileStorageStrategy;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.io.File;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class FileControllerTest {

    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Mock
    private FileStorageStrategy fileStorageStrategy;

    @Mock
    private UserService userService;

    @Mock
    private StorageProperties storageProperties;

    @InjectMocks
    private FileController fileController;

    private User loginUser;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(fileController)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();

        loginUser = new User();
        loginUser.setId(1L);
        loginUser.setUserName("testUser");

        StorageProperties.LocalConfig localConfig = new StorageProperties.LocalConfig();
        localConfig.setPath("./test-storage");
        when(storageProperties.getLocal()).thenReturn(localConfig);
    }

    // ==================== 头像上传测试（已有功能回归） ====================

    @Test
    void uploadAvatar_shouldSucceed() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(fileStorageStrategy.uploadFile(anyString(), any(File.class)))
                .thenReturn("http://localhost:8700/api/storage/avatars/2026/06/27/test.png");

        MockMultipartFile file = new MockMultipartFile(
                "file", "avatar.png", "image/png", "fake-image-content".getBytes());

        mockMvc.perform(multipart("/file/upload/avatar")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    void uploadAvatar_shouldRejectOversizedFile() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        byte[] largeContent = new byte[3 * 1024 * 1024]; // 3MB > 2MB
        MockMultipartFile file = new MockMultipartFile(
                "file", "large.png", "image/png", largeContent);

        mockMvc.perform(multipart("/file/upload/avatar")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()));
    }

    // ==================== 聊天附件上传 — 边界测试 ====================

    @Test
    void uploadChatAttachment_shouldRejectNoFiles() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        mockMvc.perform(multipart("/file/upload/chat-attachment"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()));
    }

    @Test
    void uploadChatAttachment_shouldRejectTooManyFiles() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        MockMultipartFile[] files = new MockMultipartFile[6];
        for (int i = 0; i < 6; i++) {
            files[i] = new MockMultipartFile(
                    "files", "file" + i + ".txt", "text/plain", "content".getBytes());
        }

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(files[0]).file(files[1]).file(files[2])
                        .file(files[3]).file(files[4]).file(files[5]))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("最多上传")));
    }

    @Test
    void uploadChatAttachment_shouldRejectFileExceeding10MB() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        byte[] largeContent = new byte[11 * 1024 * 1024]; // 11MB > 10MB
        MockMultipartFile file = new MockMultipartFile(
                "files", "large.pdf", "application/pdf", largeContent);

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("不能超过 10MB")));
    }

    @Test
    void uploadChatAttachment_shouldRejectTotalExceeding30MB() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        byte[] fileContent = new byte[7 * 1024 * 1024]; // 7MB each, 5 files = 35MB > 30MB
        MockMultipartFile file1 = new MockMultipartFile(
                "files", "file1.bin", "application/octet-stream", fileContent);
        MockMultipartFile file2 = new MockMultipartFile(
                "files", "file2.bin", "application/octet-stream", fileContent);
        MockMultipartFile file3 = new MockMultipartFile(
                "files", "file3.bin", "application/octet-stream", fileContent);
        MockMultipartFile file4 = new MockMultipartFile(
                "files", "file4.bin", "application/octet-stream", fileContent);
        MockMultipartFile file5 = new MockMultipartFile(
                "files", "file5.bin", "application/octet-stream", fileContent);

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file1).file(file2).file(file3).file(file4).file(file5))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("总大小不能超过 30MB")));
    }

    @ParameterizedTest
    @ValueSource(strings = {"video/mp4", "audio/mp3", "application/x-msdownload"})
    void uploadChatAttachment_shouldRejectUnsupportedMimeType(String mimeType) throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        MockMultipartFile file = new MockMultipartFile(
                "files", "unsupported.bin", mimeType, "content".getBytes());

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("不支持的文件类型")));
    }

    @Test
    void uploadChatAttachment_shouldRejectUnsupportedExtension() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        MockMultipartFile file = new MockMultipartFile(
                "files", "malware.exe", "application/octet-stream", "evil".getBytes());

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("不支持的文件类型")));
    }

    @Test
    void uploadChatAttachment_shouldSucceedWithImage() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(fileStorageStrategy.uploadFile(anyString(), any(File.class)))
                .thenReturn("http://localhost:8700/api/storage/chat_attachments/2026/06/27/test.png");
        when(fileStorageStrategy.getStrategyType()).thenReturn("local");

        MockMultipartFile file = new MockMultipartFile(
                "files", "screenshot.png", "image/png", "fake-png-content".getBytes());

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data[0].fileName").value("screenshot.png"))
                .andExpect(jsonPath("$.data[0].mimeType").value("image/png"))
                .andExpect(jsonPath("$.data[0].storageType").value("local"));
    }

    @Test
    void uploadChatAttachment_shouldSucceedWithCodeFile() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(fileStorageStrategy.uploadFile(anyString(), any(File.class)))
                .thenReturn("http://localhost:8700/api/storage/chat_attachments/2026/06/27/test.py");
        when(fileStorageStrategy.getStrategyType()).thenReturn("local");

        MockMultipartFile file = new MockMultipartFile(
                "files", "main.py", "text/x-python", "print('hello')".getBytes());

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].fileName").value("main.py"))
                .andExpect(jsonPath("$.data[0].storageType").value("local"));
    }

    @Test
    void uploadChatAttachment_shouldHandleMixedFilesSuccessfully() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);
        when(fileStorageStrategy.uploadFile(anyString(), any(File.class)))
                .thenReturn("http://localhost:8700/api/storage/chat_attachments/2026/06/27/test.png");
        when(fileStorageStrategy.getStrategyType()).thenReturn("local");

        MockMultipartFile file1 = new MockMultipartFile(
                "files", "screenshot.png", "image/png", "png-content".getBytes());
        MockMultipartFile file2 = new MockMultipartFile(
                "files", "utils.py", "text/x-python", "def util(): pass".getBytes());
        MockMultipartFile file3 = new MockMultipartFile(
                "files", "README.md", "text/markdown", "# Hello".getBytes());

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file1).file(file2).file(file3))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.length()").value(3));
    }

    @Test
    void uploadChatAttachment_shouldRejectEmptyFile() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        MockMultipartFile file = new MockMultipartFile(
                "files", "empty.txt", "text/plain", new byte[0]);

        mockMvc.perform(multipart("/file/upload/chat-attachment")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.PARAMS_ERROR.getCode()))
                .andExpect(jsonPath("$.message").value(containsString("不能为空")));
    }

    // ==================== 聊天附件文件服务测试 ====================

    @Test
    void serveChatAttachment_shouldDenyPathTraversal() throws Exception {
        when(userService.getLoginUser(any())).thenReturn(loginUser);

        // path traversal attempt
        mockMvc.perform(get("/file/chat-attachment/../../etc/passwd"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(ErrorCode.NOT_FOUND_ERROR.getCode()));
    }
}
