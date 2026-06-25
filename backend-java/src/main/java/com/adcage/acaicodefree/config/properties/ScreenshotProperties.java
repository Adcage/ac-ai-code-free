package com.adcage.acaicodefree.config.properties;

import com.adcage.acaicodefree.model.enums.BrowserTypeEnum;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.screenshot")
public class ScreenshotProperties {

    private String tempDir;

    private Integer width;

    private Integer height;

    private Long waitAfterLoadMillis;

    private Float compressionQuality;

    private String uploadPrefix;

    private Integer maxRetries;

    private Long retryDelayMillis;

    /**
     * 浏览器类型：chrome, edge, firefox
     */
    private String browser = "chrome";

    /**
     * 封面兜底扫描间隔（分钟），默认 5
     */
    private Integer coverScanIntervalMinutes = 5;

    /**
     * 封面兜底扫描回溯时间（小时），默认 24
     */
    private Integer coverScanLookbackHours = 24;

    public String getTempDir() {
        return tempDir;
    }

    public void setTempDir(String tempDir) {
        this.tempDir = tempDir;
    }

    public Integer getWidth() {
        return width;
    }

    public void setWidth(Integer width) {
        this.width = width;
    }

    public Integer getHeight() {
        return height;
    }

    public void setHeight(Integer height) {
        this.height = height;
    }

    public Long getWaitAfterLoadMillis() {
        return waitAfterLoadMillis;
    }

    public void setWaitAfterLoadMillis(Long waitAfterLoadMillis) {
        this.waitAfterLoadMillis = waitAfterLoadMillis;
    }

    public Float getCompressionQuality() {
        return compressionQuality;
    }

    public void setCompressionQuality(Float compressionQuality) {
        this.compressionQuality = compressionQuality;
    }

    public String getUploadPrefix() {
        return uploadPrefix;
    }

    public void setUploadPrefix(String uploadPrefix) {
        this.uploadPrefix = uploadPrefix;
    }

    public Integer getMaxRetries() {
        return maxRetries;
    }

    public void setMaxRetries(Integer maxRetries) {
        this.maxRetries = maxRetries;
    }

    public Long getRetryDelayMillis() {
        return retryDelayMillis;
    }

    public void setRetryDelayMillis(Long retryDelayMillis) {
        this.retryDelayMillis = retryDelayMillis;
    }

    public String getBrowser() {
        return browser;
    }

    public void setBrowser(String browser) {
        this.browser = browser;
    }

    public Integer getCoverScanIntervalMinutes() {
        return coverScanIntervalMinutes;
    }

    public void setCoverScanIntervalMinutes(Integer coverScanIntervalMinutes) {
        this.coverScanIntervalMinutes = coverScanIntervalMinutes;
    }

    public Integer getCoverScanLookbackHours() {
        return coverScanLookbackHours;
    }

    public void setCoverScanLookbackHours(Integer coverScanLookbackHours) {
        this.coverScanLookbackHours = coverScanLookbackHours;
    }

    /**
     * 获取浏览器类型枚举
     *
     * @return 浏览器类型枚举
     */
    public BrowserTypeEnum getBrowserType() {
        return BrowserTypeEnum.getEnumByValue(browser);
    }
}
