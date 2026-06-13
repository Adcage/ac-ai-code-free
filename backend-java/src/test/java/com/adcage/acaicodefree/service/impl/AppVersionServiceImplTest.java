package com.adcage.acaicodefree.service.impl;

import com.adcage.acaicodefree.model.entity.AppVersion;
import com.adcage.acaicodefree.service.AppVersionService;
import com.mybatisflex.annotation.Column;
import com.mybatisflex.core.query.QueryWrapper;
import jakarta.annotation.Resource;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
@ActiveProfiles("local")
@TestPropertySource(properties = "grpc.server.port=0")
class AppVersionServiceImplTest {

    @Resource
    private AppVersionService appVersionService;

    @Test
    void appVersionColumnMapping_ShouldMatchCamelCaseDatabaseColumns() throws NoSuchFieldException {
        Map<String, String> expectedColumns = Map.of(
                "appId", "appId",
                "agentRunId", "agentRunId",
                "versionNo", "versionNo",
                "sourcePath", "sourcePath",
                "buildPath", "buildPath",
                "createTime", "createTime"
        );

        for (Map.Entry<String, String> entry : expectedColumns.entrySet()) {
            Column column = AppVersion.class.getDeclaredField(entry.getKey()).getAnnotation(Column.class);
            assertNotNull(column, entry.getKey() + " 缺少 @Column 注解");
            assertEquals(entry.getValue(), column.value(), entry.getKey() + " 数据库列名映射错误");
        }
    }

    @Test
    void createAppVersion_ShouldPersistAndIncrementVersionNoWithCamelCaseColumns() {
        long appId = 900_000_000_000L + System.nanoTime();
        try {
            Long firstId = appVersionService.createAppVersion(appId, appId + 1, "/tmp/source-1", "/tmp/dist-1");
            Long secondId = appVersionService.createAppVersion(appId, appId + 2, "/tmp/source-2", "/tmp/dist-2");

            AppVersion first = appVersionService.getById(firstId);
            AppVersion second = appVersionService.getById(secondId);

            assertNotNull(first);
            assertNotNull(second);
            assertEquals(1, first.getVersionNo());
            assertEquals(2, second.getVersionNo());
            assertEquals("/tmp/source-2", second.getSourcePath());
            assertEquals("/tmp/dist-2", second.getBuildPath());
        } finally {
            appVersionService.remove(QueryWrapper.create().eq("appId", appId));
        }
    }
}
