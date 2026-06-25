package com.adcage.acaicodefree.legacy.workflow.state;

import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.legacy.workflow.model.ImageCollectionPlan;
import com.adcage.acaicodefree.legacy.workflow.model.ImageResource;
import com.adcage.acaicodefree.legacy.workflow.model.QualityResult;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;
import org.bsc.langgraph4j.state.Channel;
import org.bsc.langgraph4j.state.Channels;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Slf4j
@Deprecated
public class WorkflowContext implements Serializable {

    public static final String STATE_KEY = "workflowContext";

    private Long appId;
    private String currentStep;
    private String originalPrompt;
    private String imageListStr;

    @Builder.Default
    private List<ImageResource> imageList = new ArrayList<>();

    private ImageCollectionPlan imageCollectionPlan;

    @Builder.Default
    private List<ImageResource> contentImages = new ArrayList<>();

    @Builder.Default
    private List<ImageResource> illustrations = new ArrayList<>();

    @Builder.Default
    private List<ImageResource> diagrams = new ArrayList<>();

    @Builder.Default
    private List<ImageResource> logos = new ArrayList<>();

    private String enhancedPrompt;
    private CodeGenTypeEnum generationType;
    private String generatedCodeDir;
    private String buildResultDir;
    private QualityResult qualityResult;
    private String errorMessage;

    public static Map<String, Channel<?>> schema() {
        return Map.of(
                STATE_KEY, Channels.base(WorkflowContext::new)
        );
    }

    public static WorkflowContext fromState(AgentState state) {
        return state.value(STATE_KEY, new WorkflowContext());
    }

    public Map<String, Object> toStateUpdate() {
        return Map.of(STATE_KEY, this);
    }

    public void addError(String error) {
        this.errorMessage = error;
        log.error("[WorkflowContext] error at step '{}': {}", currentStep, error);
    }

    public void advanceStep(String step) {
        log.info("[WorkflowContext] step transition: {} -> {}", currentStep, step);
        this.currentStep = step;
    }
}
