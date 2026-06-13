package com.adcage.acaicodefree.ai;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import dev.langchain4j.service.SystemMessage;

/**
 * @deprecated Java AI 路由已禁用，后续智能路由必须迁移到 Python Agent Runtime。
 */
@Deprecated(since = "2026-06-13", forRemoval = false)
public interface AiCodeGenTypeRoutingService {

    @SystemMessage(fromResource = "prompt/codegen-routing-system-prompt.txt")
    CodeGenTypeEnum routeCodeGenType(String userPrompt);
}
