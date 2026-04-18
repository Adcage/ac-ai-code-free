package com.adcage.acaicodefree.ai.model.message;

import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class ToolExecutedMessage extends StreamMessage {

    private String id;

    private String name;

    private String arguments;

    private String result;

    public ToolExecutedMessage(String id, String name, String arguments, String result) {
        super(StreamMessageTypeEnum.TOOL_EXECUTED.getValue());
        this.id = id;
        this.name = name;
        this.arguments = arguments;
        this.result = result;
    }
}
