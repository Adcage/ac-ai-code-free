package com.adcage.acaicodefree.ai.model.message;

public enum StreamMessageTypeEnum {
    AI_RESPONSE("ai_response"),
    TOOL_REQUEST("tool_request"),
    TOOL_EXECUTED("tool_executed"),
    STATUS("status");

    private final String value;

    StreamMessageTypeEnum(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}
