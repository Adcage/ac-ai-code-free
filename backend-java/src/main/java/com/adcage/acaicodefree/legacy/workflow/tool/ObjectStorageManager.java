package com.adcage.acaicodefree.legacy.workflow.tool;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.StorageProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.manager.CosManager;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

public class ObjectStorageManager {

    private final StorageProperties storageProperties;

    private final CosManager cosManager;

    public ObjectStorageManager(StorageProperties storageProperties, CosManager cosManager) {
        this.storageProperties = storageProperties;
        this.cosManager = cosManager;
    }

    public String uploadFile(String objectKey, File file) {
        validateSourceFile(file);
        String normalizedKey = normalizeObjectKey(objectKey);
        if (isCosStorage()) {
            if (cosManager == null) {
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "COS 存储未正确初始化");
            }
            return cosManager.uploadFile(normalizedKey, file);
        }
        return uploadToLocal(normalizedKey, file);
    }

    private boolean isCosStorage() {
        return StrUtil.equalsIgnoreCase("cos", storageProperties.getType());
    }

    private void validateSourceFile(File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "上传文件不存在");
        }
    }

    private String uploadToLocal(String objectKey, File file) {
        String localRoot = storageProperties.getLocal().getPath();
        if (StrUtil.isBlank(localRoot)) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "本地存储路径未配置");
        }
        Path targetPath = Path.of(localRoot, objectKey.substring(1));
        try {
            Files.createDirectories(targetPath.getParent());
            Files.copy(file.toPath(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "本地文件上传失败: " + e.getMessage());
        }
        return buildLocalUrl(objectKey);
    }

    private String buildLocalUrl(String objectKey) {
        String urlPrefix = StrUtil.removeSuffix(StrUtil.blankToDefault(storageProperties.getLocal().getUrlPrefix(), ""), "/");
        return urlPrefix + objectKey;
    }

    private String normalizeObjectKey(String objectKey) {
        String normalizedKey = StrUtil.blankToDefault(objectKey, "").replace('\\', '/');
        if (!normalizedKey.startsWith("/")) {
            normalizedKey = "/" + normalizedKey;
        }
        return normalizedKey;
    }
}
