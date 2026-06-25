package com.adcage.acaicodefree.legacy.ai.tools;

import cn.hutool.core.util.StrUtil;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.Map;

@Component
@Deprecated
public class ToolManager {

    @Resource
    private BaseTool[] tools;

    private final Map<String, BaseTool> toolMap = new LinkedHashMap<>();

    @PostConstruct
    public void init() {
        toolMap.clear();
        if (tools == null || tools.length == 0) {
            return;
        }
        for (BaseTool tool : tools) {
            if (tool == null || StrUtil.isBlank(tool.getToolName())) {
                continue;
            }
            if (toolMap.containsKey(tool.getToolName())) {
                throw new IllegalStateException("检测到重复工具名: " + tool.getToolName());
            }
            toolMap.put(tool.getToolName(), tool);
        }
    }

    public BaseTool getTool(String toolName) {
        if (StrUtil.isBlank(toolName)) {
            return null;
        }
        return toolMap.get(toolName);
    }

    public Object[] getAllTools() {
        return toolMap.values().toArray();
    }
}
