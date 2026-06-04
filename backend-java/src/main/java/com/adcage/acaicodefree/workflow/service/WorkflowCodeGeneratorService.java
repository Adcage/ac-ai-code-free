package com.adcage.acaicodefree.workflow.service;

import com.adcage.acaicodefree.core.AiCodeGeneratorFacade;
import com.adcage.acaicodefree.workflow.ai.ImageCollectionPlanServiceFactory;
import com.adcage.acaicodefree.workflow.ai.ImageCollectionServiceFactory;
import com.adcage.acaicodefree.workflow.ai.PromptEnhancerServiceFactory;
import com.adcage.acaicodefree.workflow.config.WorkflowProperties;
import com.adcage.acaicodefree.workflow.node.CodeGeneratorNode;
import com.adcage.acaicodefree.workflow.node.CodeQualityCheckNode;
import com.adcage.acaicodefree.workflow.node.ImageCollectorNode;
import com.adcage.acaicodefree.workflow.node.ProjectBuilderNode;
import com.adcage.acaicodefree.workflow.node.PromptEnhancerNode;
import com.adcage.acaicodefree.workflow.node.RouterNode;
import com.adcage.acaicodefree.workflow.node.concurrent.ContentImageCollectorNode;
import com.adcage.acaicodefree.workflow.node.concurrent.DiagramCollectorNode;
import com.adcage.acaicodefree.workflow.node.concurrent.ImageAggregatorNode;
import com.adcage.acaicodefree.workflow.node.concurrent.ImagePlanNode;
import com.adcage.acaicodefree.workflow.node.concurrent.IllustrationCollectorNode;
import com.adcage.acaicodefree.workflow.node.concurrent.LogoCollectorNode;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import com.adcage.acaicodefree.workflow.tool.ImageSearchTool;
import com.adcage.acaicodefree.workflow.tool.LogoGeneratorTool;
import com.adcage.acaicodefree.workflow.tool.MermaidDiagramTool;
import com.adcage.acaicodefree.workflow.tool.UndrawIllustrationTool;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

@Slf4j
@Service
public class WorkflowCodeGeneratorService {

    @Resource
    private WorkflowProperties workflowProperties;

    @Resource
    private ImageCollectionServiceFactory imageCollectionServiceFactory;

    @Resource
    private PromptEnhancerServiceFactory promptEnhancerServiceFactory;

    @Resource
    private ImageCollectionPlanServiceFactory imageCollectionPlanServiceFactory;

    @Resource
    private AiCodeGeneratorFacade aiCodeGeneratorFacade;

    @Resource
    private ImageSearchTool imageSearchTool;

    @Resource
    private UndrawIllustrationTool undrawIllustrationTool;

    @Resource
    private MermaidDiagramTool mermaidDiagramTool;

    @Resource
    private LogoGeneratorTool logoGeneratorTool;

    public WorkflowContext executeWorkflow(Long appId, String message) throws Exception {
        if (workflowProperties.isEnableParallelImageCollect()) {
            return buildConcurrentWorkflow().execute(appId, message);
        }
        CodeGenWorkflow workflow = new CodeGenWorkflow(
                new ImageCollectorNode(imageCollectionServiceFactory.createService(), workflowProperties.getImageSummaryLimit()),
                new PromptEnhancerNode(promptEnhancerServiceFactory.createService()),
                new RouterNode(),
                new CodeGeneratorNode(aiCodeGeneratorFacade),
                new CodeQualityCheckNode(),
                new ProjectBuilderNode()
        );
        return workflow.execute(appId, message);
    }

    public Flux<String> executeWorkflowWithFlux(Long appId, String message) {
        return executeWorkflowEventFlux(appId, message)
                .map(event -> event.event() + ":" + event.data());
    }

    public Flux<WorkflowStreamEvent> executeWorkflowEventFlux(Long appId, String message) {
        return Flux.create(sink -> {
            sink.next(new WorkflowStreamEvent("workflow_start", "{\"step\":\"start\",\"appId\":" + appId + "}"));
            try {
                WorkflowContext context = executeWorkflow(appId, message);
                sink.next(new WorkflowStreamEvent("step_completed", "{\"step\":\"image_collect\"}"));
                sink.next(new WorkflowStreamEvent("step_completed", "{\"step\":\"prompt_enhancer\"}"));
                sink.next(new WorkflowStreamEvent("step_completed", "{\"step\":\"router\"}"));
                sink.next(new WorkflowStreamEvent("step_completed", "{\"step\":\"code_generator\"}"));
                sink.next(new WorkflowStreamEvent("step_completed", "{\"step\":\"code_quality_check\"}"));
                sink.next(new WorkflowStreamEvent("workflow_completed", "{\"step\":\"done\",\"generatedCodeDir\":\""
                        + context.getGeneratedCodeDir().replace("\\", "\\\\") + "\"}"));
                sink.complete();
            } catch (Exception e) {
                log.error("[WorkflowCodeGeneratorService] workflow execution failed, appId={}", appId, e);
                sink.next(new WorkflowStreamEvent("workflow_error", "{\"message\":\""
                        + (e.getMessage() == null ? "unknown" : e.getMessage().replace("\"", "'")) + "\"}"));
                sink.complete();
            }
        });
    }

    private CodeGenConcurrentWorkflow buildConcurrentWorkflow() {
        return new CodeGenConcurrentWorkflow(
                new ImagePlanNode(imageCollectionPlanServiceFactory.createService()),
                new ContentImageCollectorNode(query -> imageSearchTool.search(query)),
                new IllustrationCollectorNode(query -> undrawIllustrationTool.search(query, workflowProperties.getMaxImageCount())),
                new DiagramCollectorNode(query -> mermaidDiagramTool.renderArchitectureDiagram(query, query)),
                new LogoCollectorNode(query -> logoGeneratorTool.generateLogo(query)),
                new ImageAggregatorNode()
        );
    }
}
