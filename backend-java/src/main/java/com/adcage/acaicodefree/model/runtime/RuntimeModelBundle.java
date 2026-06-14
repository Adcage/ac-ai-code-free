package com.adcage.acaicodefree.model.runtime;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeModelBundle {
    private boolean success;
    private String errorMessage;
    private List<RuntimeModelConfig> configs;
    private String policyVersion;
    private String billingContext;
}
