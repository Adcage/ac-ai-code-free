package com.adcage.acaicodefree.service;

import com.mybatisflex.core.service.IService;
import com.adcage.acaicodefree.model.entity.AppVersion;

public interface AppVersionService extends IService<AppVersion> {

    int getNextVersionNo(Long appId);

    Long createAppVersion(Long appId, Long agentRunId, String sourcePath, String buildPath);
}
