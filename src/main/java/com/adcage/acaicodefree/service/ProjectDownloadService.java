package com.adcage.acaicodefree.service;

import jakarta.servlet.http.HttpServletResponse;

import java.nio.file.Path;

public interface ProjectDownloadService {

    /**
     * 将指定目录压缩并写入响应
     *
     * @param sourceDir 源码目录
     * @param fileName 下载文件名
     * @param response HTTP 响应
     */
    void writeProjectZipToResponse(Path sourceDir, String fileName, HttpServletResponse response);
}
