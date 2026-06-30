package com.adcage.acaicodefree.utils;

import cn.hutool.core.util.StrUtil;

import java.util.regex.Pattern;

/**
 * AI 标题生成相关的兜底与清洗工具。
 */
public final class AiTitleUtils {

    private static final Pattern DEFAULT_SESSION_TITLE_PATTERN = Pattern.compile("^新会话\\s*\\d+$");
    private static final Pattern LEADING_REQUEST_PREFIX = Pattern.compile(
            "^(请帮我|帮我|请|我想做一个|我想做一款|我想要一个|做一个|做一款|生成一个|生成一款|创建一个|创建一款)+"
    );
    private static final Pattern TITLE_PREFIX = Pattern.compile("^(标题|应用名|应用标题|会话名|会话标题)\\s*[:：-]\\s*");

    private AiTitleUtils() {
    }

    public static String fallbackAppTitle(String initPrompt) {
        String normalized = StrUtil.blankToDefault(initPrompt, "").replace('\r', '\n');
        String firstLine = normalized.split("\n")[0];
        String firstClause = firstLine.split("[，。,；;！!？?]", 2)[0];
        String candidate = LEADING_REQUEST_PREFIX.matcher(firstClause.trim()).replaceFirst("");
        String sanitized = sanitizeTitle(candidate, 12);
        return StrUtil.isBlank(sanitized) ? "未命名应用" : sanitized;
    }

    public static String sanitizeTitle(String rawTitle, int maxLength) {
        if (StrUtil.isBlank(rawTitle)) {
            return "";
        }
        String sanitized = rawTitle.lines()
                .map(String::trim)
                .map(line -> TITLE_PREFIX.matcher(line).replaceFirst(""))
                .map(line -> line.replaceAll("^[\\-*#\\s]+", "").trim())
                .filter(StrUtil::isNotBlank)
                .findFirst()
                .orElse("");
        sanitized = sanitized.strip();
        sanitized = StrUtil.removePrefix(sanitized, "\"");
        sanitized = StrUtil.removeSuffix(sanitized, "\"");
        sanitized = sanitized.replaceAll("^[“”‘’`【\\[]+|[“”‘’`】\\]]+$", "");
        sanitized = sanitized.replaceAll("\\s+", " ").trim();
        sanitized = sanitized.replaceAll("[：:。；;，,]+$", "").trim();
        if (maxLength > 0 && sanitized.length() > maxLength) {
            sanitized = sanitized.substring(0, maxLength).trim();
        }
        return sanitized;
    }

    public static String sanitizeAppTitle(String rawTitle) {
        return sanitizeTitle(rawTitle, 12);
    }

    public static String sanitizeSessionTitle(String rawTitle) {
        return sanitizeTitle(rawTitle, 18);
    }

    public static boolean isDefaultSessionTitle(String title) {
        return StrUtil.isNotBlank(title) && DEFAULT_SESSION_TITLE_PATTERN.matcher(title.trim()).matches();
    }

    public static String buildDefaultSessionTitle(long sessionIndex) {
        return "新会话 " + sessionIndex;
    }
}
