package com.adcage.acaicodefree.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import jakarta.annotation.Resource;

@Slf4j
@Component
public class SchemaCompatibilityInitializer implements ApplicationRunner {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(ApplicationArguments args) {
        ensureColumn("app", "styleTemplate", "ALTER TABLE app ADD COLUMN styleTemplate VARCHAR(64) NULL COMMENT 'style template'");
        ensureColumn("app", "deployKey", "ALTER TABLE app ADD COLUMN deployKey VARCHAR(64) NULL COMMENT 'deploy key'");
        ensureColumn("app", "deployedTime", "ALTER TABLE app ADD COLUMN deployedTime DATETIME NULL COMMENT 'deployed time'");
        ensureIndex("app", "uk_deployKey", "ALTER TABLE app ADD UNIQUE KEY uk_deployKey (deployKey)");
    }

    private void ensureColumn(String tableName, String columnName, String ddl) {
        Long count = jdbcTemplate.queryForObject(
                """
                        SELECT COUNT(*)
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE()
                          AND table_name = ?
                          AND column_name = ?
                        """,
                Long.class,
                tableName,
                columnName
        );
        if (count != null && count > 0) {
            return;
        }
        jdbcTemplate.execute(ddl);
        log.info("Applied schema compatibility column: {}.{}", tableName, columnName);
    }

    private void ensureIndex(String tableName, String indexName, String ddl) {
        Long count = jdbcTemplate.queryForObject(
                """
                        SELECT COUNT(*)
                        FROM information_schema.statistics
                        WHERE table_schema = DATABASE()
                          AND table_name = ?
                          AND index_name = ?
                        """,
                Long.class,
                tableName,
                indexName
        );
        if (count != null && count > 0) {
            return;
        }
        jdbcTemplate.execute(ddl);
        log.info("Applied schema compatibility index: {}.{}", tableName, indexName);
    }
}
