package com.adcage.acaicodefree.model.runtime;

import cn.hutool.core.util.StrUtil;

import java.net.URI;
import java.util.Locale;

/**
 * 运行时模型 Base URL 只做安全标准化，不猜测供应商版本路径。
 * <p>
 * 兼容目标：
 * 1. 允许根路径，例如 https://api.example.com
 * 2. 允许任意版本路径，例如 /v1、/v4、/openai/v1
 * 3. 去掉尾部斜杠，避免下游 SDK 再拼接时出现双斜杠
 * 4. 折叠 path 中连续的多个斜杠
 */
public final class RuntimeModelUrlNormalizer {

    private RuntimeModelUrlNormalizer() {
    }

    public static String normalize(String rawBaseUrl) {
        if (StrUtil.isBlank(rawBaseUrl)) {
            return "";
        }

        String trimmed = StrUtil.trim(rawBaseUrl);
        URI uri = URI.create(trimmed);

        String scheme = StrUtil.blankToDefault(uri.getScheme(), "").toLowerCase(Locale.ROOT);
        String authority = uri.getRawAuthority();

        String normalizedPath = normalizePath(uri.getRawPath());
        StringBuilder builder = new StringBuilder()
                .append(scheme)
                .append("://")
                .append(StrUtil.blankToDefault(authority, ""));
        if (StrUtil.isNotBlank(normalizedPath)) {
            if (!normalizedPath.startsWith("/")) {
                builder.append('/');
            }
            builder.append(normalizedPath);
        }
        if (StrUtil.isNotBlank(uri.getRawQuery())) {
            builder.append('?').append(uri.getRawQuery());
        }
        if (StrUtil.isNotBlank(uri.getRawFragment())) {
            builder.append('#').append(uri.getRawFragment());
        }
        return builder.toString();
    }

    public static boolean isSupportedHttpUrl(String rawBaseUrl) {
        if (StrUtil.isBlank(rawBaseUrl)) {
            return false;
        }
        try {
            URI uri = URI.create(StrUtil.trim(rawBaseUrl));
            String scheme = StrUtil.blankToDefault(uri.getScheme(), "").toLowerCase(Locale.ROOT);
            return ("http".equals(scheme) || "https".equals(scheme))
                    && StrUtil.isNotBlank(uri.getRawAuthority());
        } catch (Exception e) {
            return false;
        }
    }

    private static String normalizePath(String rawPath) {
        String path = StrUtil.blankToDefault(rawPath, "");
        if (path.isEmpty()) {
            return "";
        }

        path = path.replaceAll("/{2,}", "/");
        if (path.length() > 1 && path.endsWith("/")) {
            path = path.substring(0, path.length() - 1);
        }
        if ("/".equals(path)) {
            return "";
        }
        return path;
    }
}
