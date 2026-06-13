package com.adcage.acaicodefree.legacy.workflow.tool;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.legacy.workflow.model.ImageCategoryEnum;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public class UndrawIllustrationTool {

    private static final Pattern IMG_PATTERN = Pattern.compile("<img[^>]*src=\\\"([^\\\"]+)\\\"[^>]*alt=\\\"([^\\\"]*)\\\"[^>]*>", Pattern.CASE_INSENSITIVE);

    @FunctionalInterface
    public interface HtmlFetcher {
        String fetch(String keyword, int limit) throws Exception;
    }

    private final HtmlFetcher htmlFetcher;

    public UndrawIllustrationTool(HtmlFetcher htmlFetcher) {
        this.htmlFetcher = htmlFetcher;
    }

    public List<ImageResource> search(String keyword, int limit) {
        if (StrUtil.isBlank(keyword) || limit <= 0) {
            return Collections.emptyList();
        }
        try {
            String html = htmlFetcher.fetch(keyword, limit);
            return parseHtml(html, keyword, limit);
        } catch (Exception e) {
            log.warn("[UndrawIllustrationTool] search failed, keyword={}, limit={}", keyword, limit, e);
            return Collections.emptyList();
        }
    }

    private List<ImageResource> parseHtml(String html, String keyword, int limit) {
        if (StrUtil.isBlank(html)) {
            return Collections.emptyList();
        }
        List<ImageResource> results = new ArrayList<>();
        Matcher matcher = IMG_PATTERN.matcher(html);
        while (matcher.find() && results.size() < limit) {
            String url = matcher.group(1);
            if (StrUtil.isBlank(url)) {
                continue;
            }
            String description = StrUtil.blankToDefault(matcher.group(2), keyword + " illustration");
            results.add(ImageResource.builder()
                    .category(ImageCategoryEnum.ILLUSTRATION)
                    .description(description)
                    .url(url)
                    .build());
        }
        return results;
    }
}
