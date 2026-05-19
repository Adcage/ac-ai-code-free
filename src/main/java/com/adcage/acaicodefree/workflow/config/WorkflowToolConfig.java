package com.adcage.acaicodefree.workflow.config;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.http.HttpUtil;
import com.adcage.acaicodefree.config.properties.StorageProperties;
import com.adcage.acaicodefree.manager.CosManager;
import com.adcage.acaicodefree.workflow.tool.ImageSearchTool;
import com.adcage.acaicodefree.workflow.tool.LogoGeneratorTool;
import com.adcage.acaicodefree.workflow.tool.MermaidDiagramTool;
import com.adcage.acaicodefree.workflow.tool.ObjectStorageManager;
import com.adcage.acaicodefree.workflow.tool.UndrawIllustrationTool;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

@Configuration
public class WorkflowToolConfig {

    @Bean
    public ObjectStorageManager objectStorageManager(StorageProperties storageProperties,
                                                     ObjectProvider<CosManager> cosManagerProvider) {
        return new ObjectStorageManager(storageProperties, cosManagerProvider.getIfAvailable());
    }

    @Bean
    public ImageSearchTool imageSearchTool(@Value("${pexels.api-key:}") String apiKey,
                                           WorkflowProperties workflowProperties) {
        return new ImageSearchTool(apiKey, workflowProperties.getMaxImageCount(), keyword -> {
            HttpResponse response = HttpRequest.get("https://api.pexels.com/v1/search")
                    .form(Map.of("query", keyword, "per_page", workflowProperties.getMaxImageCount()))
                    .header("Authorization", apiKey)
                    .execute();
            return response.body();
        });
    }

    @Bean
    public UndrawIllustrationTool undrawIllustrationTool() {
        return new UndrawIllustrationTool((keyword, limit) -> HttpUtil.get("https://undraw.co/search?query=" + HttpUtil.encodeParams(keyword, java.nio.charset.StandardCharsets.UTF_8)));
    }

    @Bean
    public MermaidDiagramTool mermaidDiagramTool(ObjectStorageManager objectStorageManager,
                                                 WorkflowMermaidProperties workflowMermaidProperties) {
        return new MermaidDiagramTool(objectStorageManager,
                workflowMermaidProperties.getCommand(),
                workflowMermaidProperties.getTempDir(),
                (command, outputFile) -> {
                    Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
                    return process.waitFor();
                });
    }

    @Bean
    public LogoGeneratorTool logoGeneratorTool(@Value("${dashscope.api-key:}") String apiKey,
                                               @Value("${dashscope.image-model:wanx2.2-t2i-flash}") String imageModel,
                                               WorkflowMermaidProperties workflowMermaidProperties,
                                               ObjectStorageManager objectStorageManager) {
        return new LogoGeneratorTool(apiKey,
                workflowMermaidProperties.getTempDir(),
                objectStorageManager,
                prompt -> {
                    if (StrUtil.isBlank(apiKey)) {
                        return "";
                    }
                    HttpResponse response = HttpRequest.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis")
                            .header("Authorization", "Bearer " + apiKey)
                            .header("Content-Type", "application/json")
                            .body(cn.hutool.json.JSONUtil.toJsonStr(Map.of(
                                    "model", imageModel,
                                    "input", Map.of("prompt", prompt + "，简洁现代，不要文字"),
                                    "parameters", Map.of("n", 1)
                            )))
                            .execute();
                    String body = response.body();
                    cn.hutool.json.JSONObject jsonObject = cn.hutool.json.JSONUtil.parseObj(body);
                    cn.hutool.json.JSONArray results = jsonObject.getByPath("output.results", cn.hutool.json.JSONArray.class);
                    if (results == null || results.isEmpty()) {
                        return "";
                    }
                    return cn.hutool.json.JSONUtil.parseObj(results.get(0)).getStr("url");
                },
                (url, targetFile) -> {
                    byte[] bytes = HttpUtil.downloadBytes(url);
                    Files.write(targetFile, bytes);
                });
    }
}
