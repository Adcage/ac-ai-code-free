package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.ScreenshotProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.manager.CosManager;
import com.adcage.acaicodefree.service.ScreenshotService;
import com.adcage.acaicodefree.storage.FileStorageStrategy;
import com.adcage.acaicodefree.utils.WebScreenshotUtils;
import jakarta.annotation.Resource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.File;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

@Service
public class ScreenshotServiceImpl implements ScreenshotService {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy/MM/dd");
    private static final Logger log = LoggerFactory.getLogger(ScreenshotServiceImpl.class);

    @Resource
    private FileStorageStrategy fileStorageStrategy;

    @Resource
    private ScreenshotProperties screenshotProperties;

    @Override
    public String generateAndUploadCover(Long appId, String appUrl) {
        if (appId == null || appId <= 0) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用 id 不合法");
        }
        if (StrUtil.isBlank(appUrl)) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用访问地址不能为空");
        }
        File compressedFile = null;
        try {
            compressedFile = captureCompressedFile(appUrl);
            String objectKey = buildObjectKey(compressedFile.getName());
            return fileStorageStrategy.uploadFile(objectKey, compressedFile);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("生成应用封面失败, appId={}, appUrl={}", appId, appUrl, e);
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "生成封面失败: " + e.getMessage());
        } finally {
            WebScreenshotUtils.deleteIfExists(compressedFile);
        }
    }

    File captureCompressedFile(String appUrl) throws Exception {
        return WebScreenshotUtils.captureAndCompress(appUrl,
                screenshotProperties.getTempDir(),
                screenshotProperties.getWidth(),
                screenshotProperties.getHeight(),
                screenshotProperties.getWaitAfterLoadMillis(),
                screenshotProperties.getCompressionQuality(),
                screenshotProperties.getBrowserType());
    }

    private String buildObjectKey(String fileName) {
        String prefix = StrUtil.blankToDefault(screenshotProperties.getUploadPrefix(), "/screenshots");
        if (!prefix.startsWith("/")) {
            prefix = "/" + prefix;
        }
        return prefix + "/" + DATE_FORMATTER.format(LocalDate.now()) + "/" + fileName;
    }
}
