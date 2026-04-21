package com.adcage.acaicodefree.service;

public interface ScreenshotService {

    /**
     * 根据应用访问地址生成封面并上传，返回可访问 URL
     *
     * @param appId   应用 id
     * @param appUrl  应用访问地址
     * @return 封面图 URL
     */
    String generateAndUploadCover(Long appId, String appUrl);
}
