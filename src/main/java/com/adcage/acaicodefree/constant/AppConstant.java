package com.adcage.acaicodefree.constant;

import java.io.File;
import java.nio.file.Path;

public interface AppConstant {

    String VUE_PROJECT_OUTPUT_PREFIX = "vue_project_";

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
    String CODE_OUTPUT_ROOT_DIR = System.getProperty("user.dir") + File.separator + "temp" + File.separator + "code_output";

    /**
     * 应用部署目录
     */
    String CODE_DEPLOY_ROOT_DIR = System.getProperty("user.dir") + File.separator + "temp" + File.separator + "code_deploy";

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

}
