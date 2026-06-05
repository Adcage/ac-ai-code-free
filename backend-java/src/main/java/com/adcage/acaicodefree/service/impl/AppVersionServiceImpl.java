package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.mapper.AppVersionMapper;
import com.adcage.acaicodefree.model.entity.AppVersion;
import com.adcage.acaicodefree.service.AppVersionService;
import com.mybatisflex.core.query.QueryWrapper;
import com.mybatisflex.spring.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AppVersionServiceImpl extends ServiceImpl<AppVersionMapper, AppVersion> implements AppVersionService {

    @Override
    public int getNextVersionNo(Long appId) {
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        QueryWrapper queryWrapper = QueryWrapper.create()
                .eq("appId", appId)
                .orderBy("versionNo", false)
                .limit(1);
        AppVersion latestVersion = this.getOne(queryWrapper);
        if (latestVersion == null) {
            return 1;
        }
        return latestVersion.getVersionNo() + 1;
    }

    @Override
    public Long createAppVersion(Long appId, Long agentRunId, String sourcePath, String buildPath) {
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        ThrowUtils.throwIf(agentRunId == null || agentRunId <= 0, ErrorCode.PARAMS_ERROR, "AgentRun ID 不能为空");
        int versionNo = getNextVersionNo(appId);
        AppVersion appVersion = AppVersion.builder()
                .appId(appId)
                .agentRunId(agentRunId)
                .versionNo(versionNo)
                .sourcePath(sourcePath)
                .buildPath(buildPath)
                .status("created")
                .createTime(LocalDateTime.now())
                .build();
        boolean saveResult = this.save(appVersion);
        ThrowUtils.throwIf(!saveResult, ErrorCode.OPERATION_ERROR, "创建 AppVersion 失败");
        return appVersion.getId();
    }
}
