package com.adcage.acaicodefree.constant;

import java.io.File;
import java.nio.file.Path;
import java.util.Optional;

public interface AppConstant {

    String VUE_PROJECT_OUTPUT_PREFIX = "vue_project_";
    String SINGLE_FILE_OUTPUT_PREFIX = "single_file_";
    String MULTI_FILE_OUTPUT_PREFIX = "multi-file_";

    String DIST_DIR_NAME = "dist";

    /**
     * 精选应用的优先级
     */
    Integer GOOD_APP_PRIORITY = 99;

    /**
     * 默认应用优先级
     */
    Integer DEFAULT_APP_PRIORITY = 0;

    /**
     * 应用生成目录
     */
    String PROJECT_ROOT_DIR = resolveProjectRootDir();

    String CODE_OUTPUT_ROOT_DIR = Optional.ofNullable(System.getenv("APP_CODE_OUTPUT_DIR"))
            .filter(path -> !path.isBlank())
            .orElse(PROJECT_ROOT_DIR + File.separator + "temp" + File.separator + "code_output");

    /**
     * 应用部署目录
     */
    String CODE_DEPLOY_ROOT_DIR = Optional.ofNullable(System.getenv("APP_CODE_DEPLOY_DIR"))
            .filter(path -> !path.isBlank())
            .orElse(PROJECT_ROOT_DIR + File.separator + "temp" + File.separator + "code_deploy");

    /**
     * 应用部署域名
     */
    String CODE_DEPLOY_HOST = "http://localhost";

    static Path getCodeOutputRootPath() {
        return Path.of(CODE_OUTPUT_ROOT_DIR);
    }

    static Path getCodeDeployRootPath() {
        return Path.of(CODE_DEPLOY_ROOT_DIR);
    }

    static Path getVueProjectOutputDir(Long appId) {
        return getCodeOutputRootPath().resolve(VUE_PROJECT_OUTPUT_PREFIX + appId);
    }

    static Path getSingleFileOutputDir(Long appId) {
        return getCodeOutputRootPath().resolve(SINGLE_FILE_OUTPUT_PREFIX + appId);
    }

    static Path getMultiFileOutputDir(Long appId) {
        return getCodeOutputRootPath().resolve(MULTI_FILE_OUTPUT_PREFIX + appId);
    }

    private static String resolveProjectRootDir() {
        Path userDir = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize();
        Path fileName = userDir.getFileName();
        if (fileName != null && "backend-java".equals(fileName.toString())) {
            Path parent = userDir.getParent();
            if (parent != null) {
                return parent.toString();
            }
        }
        return userDir.toString();
    }

}
