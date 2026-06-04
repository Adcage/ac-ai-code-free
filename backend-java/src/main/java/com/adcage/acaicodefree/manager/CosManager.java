package com.adcage.acaicodefree.manager;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.config.properties.CosClientProperties;
import com.adcage.acaicodefree.exception.BusinessException;
import com.qcloud.cos.COSClient;
import com.qcloud.cos.model.PutObjectRequest;
import jakarta.annotation.Resource;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.io.File;

@Component
@ConditionalOnProperty(prefix = "storage", name = "type", havingValue = "cos", matchIfMissing = true)
public class CosManager {

    @Resource
    private COSClient cosClient;

    @Resource
    private CosClientProperties cosClientProperties;

    public String uploadFile(String key, File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "上传文件不存在");
        }
        if (StrUtil.hasBlank(cosClientProperties.getBucket(), cosClientProperties.getHost())) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "COS 配置不完整，请检查 bucket 和 host");
        }
        String normalizedKey = normalizeKey(key);
        PutObjectRequest putObjectRequest = new PutObjectRequest(cosClientProperties.getBucket(), normalizedKey, file);
        cosClient.putObject(putObjectRequest);
        return buildFileUrl(normalizedKey);
    }

    private String normalizeKey(String key) {
        String normalized = StrUtil.blankToDefault(key, "");
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized;
    }

    private String buildFileUrl(String key) {
        String host = StrUtil.removeSuffix(cosClientProperties.getHost(), "/");
        return host + key;
    }
}
