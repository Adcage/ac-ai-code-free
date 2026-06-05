package com.adcage.acaicodefree.runtime;

import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.model.entity.User;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class CodeGenerationRequest {
    private Long agentRunId;
    private Long appId;
    private Long sessionId;
    private String message;
    private App app;
    private User loginUser;
}
