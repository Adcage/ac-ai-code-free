package com.adcage.acaicodefree.controller;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.BaseResponse;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.common.ResultUtils;
import com.adcage.acaicodefree.config.properties.StorageProperties;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.model.dto.chat.ChatAttachmentInfo;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.service.UserService;
import com.adcage.acaicodefree.storage.FileStorageStrategy;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

@RestController
@RequestMapping("/file")
@Slf4j
public class FileController {

    @jakarta.annotation.Resource
    private FileStorageStrategy fileStorageStrategy;

    @jakarta.annotation.Resource
    private UserService userService;

    @jakarta.annotation.Resource
    private StorageProperties storageProperties;

    private static final long MAX_AVATAR_SIZE = 2 * 1024 * 1024;

    // ==================== 聊天附件限制 ====================

    private static final long MAX_ATTACHMENT_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    private static final long MAX_ATTACHMENT_TOTAL_SIZE = 30 * 1024 * 1024; // 30MB
    private static final int MAX_ATTACHMENT_COUNT = 5;

    private static final Set<String> ALLOWED_MIME_TYPES = Set.of(
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain", "text/csv", "text/markdown",
            "application/json", "application/xml",
            "application/zip", "application/x-tar", "application/gzip"
    );

    private static final Set<String> ALLOWED_CODE_EXTENSIONS = Set.of(
            "js", "ts", "tsx", "jsx", "py", "java", "css", "html", "vue",
            "go", "rs", "c", "cpp", "sh", "sql",
            "txt", "md", "json", "xml", "yaml", "yml", "csv"
    );

    // ==================== 头像上传 ====================

    @PostMapping("/upload/avatar")
    public BaseResponse<String> uploadAvatar(@RequestParam("file") MultipartFile file,
                                              HttpServletRequest request) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "请选择头像文件");
        ThrowUtils.throwIf(file.getSize() > MAX_AVATAR_SIZE, ErrorCode.PARAMS_ERROR, "头像文件不能超过 2MB");

        String contentType = file.getContentType();
        ThrowUtils.throwIf(contentType == null || !contentType.startsWith("image/"), ErrorCode.PARAMS_ERROR, "仅支持图片文件");

        User loginUser = userService.getLoginUser(request);
        String originalFilename = file.getOriginalFilename();
        String ext = "jpg";
        if (StrUtil.isNotBlank(originalFilename) && originalFilename.contains(".")) {
            ext = originalFilename.substring(originalFilename.lastIndexOf(".") + 1).toLowerCase();
        }
        String allowedExts = "jpg,jpeg,png,gif,webp";
        ThrowUtils.throwIf(!allowedExts.contains(ext), ErrorCode.PARAMS_ERROR, "不支持的图片格式，仅支持 jpg/png/gif/webp");

        String datePath = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
        String fileName = IdUtil.fastSimpleUUID() + "." + ext;
        String key = "avatars/" + datePath + "/" + fileName;

        File tempFile = null;
        try {
            tempFile = File.createTempFile("upload-", "." + ext);
            file.transferTo(tempFile);
            String url = fileStorageStrategy.uploadFile(key, tempFile);
            log.info("头像上传成功, userId={}, url={}", loginUser.getId(), url);
            return ResultUtils.success(url);
        } catch (Exception e) {
            log.error("头像上传失败, userId={}", loginUser.getId(), e);
            throw new RuntimeException("头像上传失败: " + e.getMessage());
        } finally {
            if (tempFile != null) {
                FileUtil.del(tempFile);
            }
        }
    }

    // ==================== 聊天附件上传 ====================

    @PostMapping("/upload/chat-attachment")
    public BaseResponse<List<ChatAttachmentInfo>> uploadChatAttachment(
            @RequestParam(value = "files", required = false) MultipartFile[] files,
            HttpServletRequest request) {
        ThrowUtils.throwIf(files == null || files.length == 0, ErrorCode.PARAMS_ERROR, "请选择要上传的文件");
        ThrowUtils.throwIf(files.length > MAX_ATTACHMENT_COUNT, ErrorCode.PARAMS_ERROR, "最多上传 " + MAX_ATTACHMENT_COUNT + " 个文件");

        User loginUser = userService.getLoginUser(request);

        // 校验总大小
        long totalSize = 0;
        for (MultipartFile f : files) {
            ThrowUtils.throwIf(f == null || f.isEmpty(), ErrorCode.PARAMS_ERROR, "上传文件不能为空");
            ThrowUtils.throwIf(f.getSize() > MAX_ATTACHMENT_FILE_SIZE, ErrorCode.PARAMS_ERROR, "单个文件不能超过 10MB");
            totalSize += f.getSize();
        }
        ThrowUtils.throwIf(totalSize > MAX_ATTACHMENT_TOTAL_SIZE, ErrorCode.PARAMS_ERROR, "文件总大小不能超过 30MB");

        List<ChatAttachmentInfo> attachments = new ArrayList<>();
        String datePath = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));

        for (MultipartFile f : files) {
            String contentType = f.getContentType();
            String originalFilename = f.getOriginalFilename();
            String ext = extractExtension(originalFilename);

            // 校验文件类型
            ThrowUtils.throwIf(!isAllowedType(contentType, ext),
                    ErrorCode.PARAMS_ERROR, "不支持的文件类型: " + (originalFilename != null ? originalFilename : "未知"));

            String uuid = IdUtil.fastSimpleUUID();
            String fileName = uuid + "." + ext;
            String key = "chat_attachments/" + datePath + "/" + fileName;

            File tempFile = null;
            try {
                tempFile = File.createTempFile("upload-", "." + ext);
                f.transferTo(tempFile);
                String url = fileStorageStrategy.uploadFile(key, tempFile);

                ChatAttachmentInfo info = new ChatAttachmentInfo();
                info.setId(uuid);
                info.setFileName(originalFilename != null ? originalFilename : fileName);
                info.setFileSize(f.getSize());
                info.setMimeType(contentType != null ? contentType : "application/octet-stream");
                info.setStorageType(fileStorageStrategy.getStrategyType());
                info.setStoragePath(key);
                info.setUrl(url);
                attachments.add(info);

                log.info("聊天附件上传成功, userId={}, fileName={}, url={}", loginUser.getId(), originalFilename, url);
            } catch (Exception e) {
                log.error("聊天附件上传失败, userId={}, fileName={}", loginUser.getId(), originalFilename, e);
                throw new RuntimeException("文件上传失败: " + e.getMessage());
            } finally {
                if (tempFile != null) {
                    FileUtil.del(tempFile);
                }
            }
        }

        return ResultUtils.success(attachments);
    }

    // ==================== 聊天附件文件服务 ====================

    @GetMapping("/chat-attachment/**")
    public ResponseEntity<org.springframework.core.io.Resource> serveChatAttachment(HttpServletRequest request) {
        String requestPath = request.getRequestURI();
        // 提取 /file/chat-attachment/ 之后的部分
        String prefix = "/api/file/chat-attachment/";
        int idx = requestPath.indexOf(prefix);
        ThrowUtils.throwIf(idx < 0, ErrorCode.NOT_FOUND_ERROR, "路径无效");
        String relativePath = requestPath.substring(idx + prefix.length());
        // URL 解码
        relativePath = URLDecoder.decode(relativePath, StandardCharsets.UTF_8);

        // 安全校验：只允许 chat_attachments/ 目录下的文件
        ThrowUtils.throwIf(!relativePath.startsWith("chat_attachments/"),
                ErrorCode.NOT_FOUND_ERROR, "仅允许访问聊天附件目录");

        String basePath = storageProperties.getLocal().getPath();
        File file = new File(basePath, relativePath);
        ThrowUtils.throwIf(!file.exists() || !file.isFile(), ErrorCode.NOT_FOUND_ERROR, "文件不存在");

        // 根据 MIME 类型设置 Content-Type
        String contentType = determineContentType(file.getName());
        org.springframework.core.io.Resource resource = new FileSystemResource(file);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, contentType)
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + file.getName() + "\"")
                .body(resource);
    }

    // ==================== 私有工具方法 ====================

    private String extractExtension(String originalFilename) {
        if (StrUtil.isNotBlank(originalFilename) && originalFilename.contains(".")) {
            return originalFilename.substring(originalFilename.lastIndexOf(".") + 1).toLowerCase();
        }
        return "bin";
    }

    private boolean isAllowedType(String contentType, String extension) {
        // MIME 类型白名单
        if (contentType != null && ALLOWED_MIME_TYPES.contains(contentType.toLowerCase())) {
            return true;
        }
        // 图片 MIME
        if (contentType != null && contentType.startsWith("image/")) {
            return true;
        }
        // 代码文件扩展名白名单
        if (extension != null && ALLOWED_CODE_EXTENSIONS.contains(extension.toLowerCase())) {
            return true;
        }
        return false;
    }

    private String determineContentType(String fileName) {
        String ext = extractExtension(fileName);
        return switch (ext) {
            case "jpg", "jpeg" -> MediaType.IMAGE_JPEG_VALUE;
            case "png" -> MediaType.IMAGE_PNG_VALUE;
            case "gif" -> MediaType.IMAGE_GIF_VALUE;
            case "webp" -> "image/webp";
            case "pdf" -> MediaType.APPLICATION_PDF_VALUE;
            case "doc" -> "application/msword";
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "zip" -> "application/zip";
            case "json" -> MediaType.APPLICATION_JSON_VALUE;
            case "xml" -> MediaType.APPLICATION_XML_VALUE;
            case "csv" -> "text/csv";
            default -> MediaType.APPLICATION_OCTET_STREAM_VALUE;
        };
    }
}
