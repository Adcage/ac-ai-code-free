package com.adcage.acaicodefree.ai.model.message;

import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class AgentStartMessage extends StreamMessage {

    private String agentName;

    public AgentStartMessage(String agentName) {
        super(StreamMessageTypeEnum.AGENT_START.getValue());
        this.agentName = agentName;
    }
}
