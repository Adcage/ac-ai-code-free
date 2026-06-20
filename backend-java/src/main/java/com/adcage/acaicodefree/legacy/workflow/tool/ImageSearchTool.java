package com.adcage.acaicodefree.legacy.workflow.tool;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.legacy.workflow.model.ImageCategoryEnum;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Slf4j
public class ImageSearchTool {

    @FunctionalInterface
    public interface HttpRequester {
        String get(String keyword) throws Exception;
    }

    private final String apiKey;

    private final int perPage;

    private final HttpRequester httpRequester;

    public ImageSearchTool(String apiKey, int perPage, HttpRequester httpRequester) {
        this.apiKey = apiKey;
        this.perPage = perPage;
        this.httpRequester = httpRequester;
    }

    public List<ImageResource> search(String keyword) {
        if (StrUtil.isBlank(keyword) || StrUtil.isBlank(apiKey)) {
            return Collections.emptyList();
        }
        try {
            String responseBody = httpRequester.get(keyword);
            return parseResponse(responseBody, keyword);
        } catch (Exception e) {
            log.warn("[ImageSearchTool] search failed, keyword={}, perPage={}", keyword, perPage, e);
            return Collections.emptyList();
        }
    }

    private List<ImageResource> parseResponse(String responseBody, String keyword) {
        if (StrUtil.isBlank(responseBody)) {
            return Collections.emptyList();
        }
        JSONObject body = JSONUtil.parseObj(responseBody);
        JSONArray photos = body.getJSONArray("photos");
        if (photos == null || photos.isEmpty()) {
            return Collections.emptyList();
        }
        List<ImageResource> results = new ArrayList<>();
        for (Object photoObj : photos) {
            JSONObject photo = JSONUtil.parseObj(photoObj);
            JSONObject src = photo.getJSONObject("src");
            if (src == null) {
                continue;
            }
            String url = StrUtil.blankToDefault(src.getStr("large"), src.getStr("original"));
            if (StrUtil.isBlank(url)) {
                continue;
            }
            String description = StrUtil.blankToDefault(photo.getStr("alt"), keyword);
            results.add(ImageResource.builder()
                    .category(ImageCategoryEnum.CONTENT)
                    .description(description)
                    .url(url)
                    .build());
        }
        return results;
    }
}
