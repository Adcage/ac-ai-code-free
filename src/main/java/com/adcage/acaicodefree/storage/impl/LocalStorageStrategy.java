package com.adcage.acaicodefree.storage.impl;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.StorageProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.storage.FileStorageStrategy;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.stereotype.Component;

import java.io.File;

/**
 * 本地存储策略实现。
 * 将文件保存到本地文件系统，通过本地服务器提供访问。
 *
 * @author adcage
 */
@Slf4j
@Component
@ConditionalOnProperty(prefix = "storage", name = "type", havingValue = "local")
@EnableConfigurationProperties(StorageProperties.class)
public class LocalStorageStrategy implements FileStorageStrategy {

    @Resource
    private StorageProperties storageProperties;

    @Override
    public String uploadFile(String key, File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "上传文件不存在");
        }

        String basePath = storageProperties.getLocal().getPath();
        if (StrUtil.isBlank(basePath)) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "本地存储路径未配置");
        }

        // 规范化 key，去除开头的 /
        String normalizedKey = normalizeKey(key);

        // 构建目标文件路径
        File targetFile = new File(basePath, normalizedKey);

        // 确保父目录存在
        File parentDir = targetFile.getParentFile();
        if (parentDir != null && !parentDir.exists()) {
            boolean created = parentDir.mkdirs();
            if (!created) {
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "无法创建存储目录: " + parentDir.getAbsolutePath());
            }
        }

        // 复制文件
        try {
            FileUtil.copy(file.getAbsolutePath(), targetFile.getAbsolutePath(), true);
            log.info("文件已保存到本地: {}", targetFile.getAbsolutePath());
        } catch (Exception e) {
            log.error("本地文件保存失败: {}", targetFile.getAbsolutePath(), e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件保存失败: " + e.getMessage());
        }

        // 返回访问 URL
        return buildFileUrl(normalizedKey);
    }

    @Override
    public String getStrategyType() {
        return "local";
    }

    /**
     * 规范化 key，去除开头的 /
     */
    private String normalizeKey(String key) {
        String normalized = StrUtil.blankToDefault(key, "");
        if (normalized.startsWith("/")) {
            normalized = normalized.substring(1);
        }
        return normalized;
    }

    /**
     * 构建完整的文件访问 URL
     */
    private String buildFileUrl(String key) {
        String urlPrefix = StrUtil.removeSuffix(storageProperties.getLocal().getUrlPrefix(), "/");
        if (!key.startsWith("/")) {
            key = "/" + key;
        }
        return urlPrefix + key;
    }
}
