package com.adcage.acaicodefree.storage;

import java.io.File;

/**
 * 文件存储策略接口。
 * 定义统一的文件上传接口，支持 COS、本地存储等多种实现。
 *
 * @author adcage
 */
public interface FileStorageStrategy {

    /**
     * 上传文件
     *
     * @param key  文件路径标识（如 /screenshots/2025/04/20/xxx.jpg）
     * @param file 要上传的文件
     * @return 文件可访问的完整 URL
     */
    String uploadFile(String key, File file);

    /**
     * 获取策略类型标识
     *
     * @return 策略类型，如 "cos"、"local"
     */
    String getStrategyType();
}
