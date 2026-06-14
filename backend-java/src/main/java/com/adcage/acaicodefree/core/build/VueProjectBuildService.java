package com.adcage.acaicodefree.core.build;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.exception.BusinessException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.concurrent.TimeUnit;

@Service
public class VueProjectBuildService {

    private static final Pattern NPM_NOTARGET_PATTERN = Pattern.compile("No matching version found for ([@\\w./-]+)@([^\\s]+)");

    private static final Pattern SEMVER_PATTERN = Pattern.compile("\\d+\\.\\d+\\.\\d+");

    private Path outputRootPath = AppConstant.getCodeOutputRootPath();

    @Value("${app.ai.vue-project.install-timeout-seconds:300}")
    private int installTimeoutSeconds;

    @Value("${app.ai.vue-project.build-timeout-seconds:180}")
    private int buildTimeoutSeconds;

    public BuildResult buildVueProject(Long appId) {
        Path projectDir = outputRootPath.resolve(AppConstant.VUE_PROJECT_OUTPUT_PREFIX).resolve(String.valueOf(appId));
        if (!Files.exists(projectDir) || !Files.isDirectory(projectDir)) {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "Vue 工程目录不存在");
        }
        String npmCommand = resolveNpmCommand(System.getProperty("os.name"));
        CommandResult installResult = executeCommand(List.of(npmCommand, "install"), projectDir, installTimeoutSeconds);
        if (installResult.exitCode() != 0) {
            CommandResult repairedInstallResult = tryRepairAndReinstall(projectDir, npmCommand, installResult);
            if (repairedInstallResult == null || repairedInstallResult.exitCode() != 0) {
                throw new BusinessException(ErrorCode.OPERATION_ERROR, "npm install 失败：" + trimLog(installResult.output()));
            }
            installResult = repairedInstallResult;
        }
        CommandResult buildResult = executeCommand(List.of(npmCommand, "run", "build"), projectDir, buildTimeoutSeconds);
        if (buildResult.exitCode() != 0) {
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "npm run build 失败：" + trimLog(buildResult.output()));
        }
        Path distPath = projectDir.resolve(AppConstant.DIST_DIR_NAME);
        if (!Files.exists(distPath) || !Files.isDirectory(distPath)) {
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "构建失败：dist 目录不存在");
        }
        return new BuildResult(distPath, trimLog(installResult.output()), trimLog(buildResult.output()));
    }

    String resolveNpmCommand(String osName) {
        if (osName != null && osName.toLowerCase().contains("win")) {
            return "npm.cmd";
        }
        return "npm";
    }

    protected CommandResult executeCommand(List<String> command, Path projectDir, int timeoutSeconds) {
        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.directory(projectDir.toFile());
        processBuilder.redirectErrorStream(true);
        try {
            Process process = processBuilder.start();
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                return new CommandResult(-1, "命令执行超时：" + String.join(" ", command));
            }
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            return new CommandResult(process.exitValue(), output);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "执行构建命令失败：" + e.getMessage());
        } catch (IOException e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "执行构建命令失败：" + e.getMessage());
        }
    }

    private CommandResult tryRepairAndReinstall(Path projectDir, String npmCommand, CommandResult installResult) {
        if (installResult == null || installResult.output() == null) {
            return null;
        }
        Matcher matcher = NPM_NOTARGET_PATTERN.matcher(installResult.output());
        if (!matcher.find()) {
            return null;
        }
        String packageName = matcher.group(1);
        String latestVersion = queryLatestVersion(projectDir, npmCommand, packageName);
        if (latestVersion == null) {
            return null;
        }
        boolean replaced = replacePackageVersion(projectDir, packageName, latestVersion);
        if (!replaced) {
            return null;
        }
        return executeCommand(List.of(npmCommand, "install"), projectDir, installTimeoutSeconds);
    }

    private String queryLatestVersion(Path projectDir, String npmCommand, String packageName) {
        CommandResult viewResult = executeCommand(List.of(npmCommand, "view", packageName, "version"), projectDir, 60);
        if (viewResult.exitCode() != 0 || viewResult.output() == null) {
            return null;
        }
        Matcher versionMatcher = SEMVER_PATTERN.matcher(viewResult.output());
        String latest = null;
        while (versionMatcher.find()) {
            latest = versionMatcher.group();
        }
        return latest;
    }

    private boolean replacePackageVersion(Path projectDir, String packageName, String latestVersion) {
        Path packageJsonPath = projectDir.resolve("package.json");
        if (!Files.exists(packageJsonPath)) {
            return false;
        }
        try {
            String packageJson = Files.readString(packageJsonPath, StandardCharsets.UTF_8);
            String updated = replaceVersionField(packageJson, packageName, latestVersion);
            if (updated.equals(packageJson) && packageName.startsWith("@vue/")) {
                updated = replaceVersionField(updated, "vue", latestVersion);
                updated = replaceVersionField(updated, "@vue/compiler-sfc", latestVersion);
            }
            if (updated.equals(packageJson)) {
                return false;
            }
            Files.writeString(packageJsonPath, updated, StandardCharsets.UTF_8);
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    private String replaceVersionField(String packageJson, String packageName, String latestVersion) {
        String escapedPackageName = Pattern.quote(packageName);
        String replaceRegex = "(\\\"" + escapedPackageName + "\\\"\\s*:\\s*\\\")([^\\\"]+)(\\\")";
        return packageJson.replaceAll(replaceRegex, "$1" + latestVersion + "$3");
    }

    private String trimLog(String log) {
        if (log == null) {
            return "";
        }
        return log.length() > 1200 ? log.substring(0, 1200) : log;
    }

    public record BuildResult(Path distPath, String installLog, String buildLog) {
    }

    protected record CommandResult(int exitCode, String output) {
    }
}
