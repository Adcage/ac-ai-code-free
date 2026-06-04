package com.adcage.acaicodefree.ai.model.message;

import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class ToolRequestMessage extends StreamMessage {

    private String id;

    private String name;

    private String arguments;

    public ToolRequestMessage(String id, String name, String arguments) {
        super(StreamMessageTypeEnum.TOOL_REQUEST.getValue());
        this.id = id;
        this.name = name;
        this.arguments = arguments;
    }
}
