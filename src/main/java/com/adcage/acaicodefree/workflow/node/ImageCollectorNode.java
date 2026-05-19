package com.adcage.acaicodefree.workflow.node;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.workflow.ai.ImageCollectionPlanService;
import com.adcage.acaicodefree.workflow.ai.ImageCollectionService;
import com.adcage.acaicodefree.workflow.model.ImageCollectionPlan;
import com.adcage.acaicodefree.workflow.model.ImageResource;
import com.adcage.acaicodefree.workflow.state.WorkflowContext;
import lombok.extern.slf4j.Slf4j;
import org.bsc.langgraph4j.state.AgentState;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
public class ImageCollectorNode {

    private final ImageCollectionService imageCollectionService;

    private final ImageCollectionPlanService imageCollectionPlanService;

    private final int imageSummaryLimit;

    private final Function<String, List<ImageResource>> contentCollector;

    private final Function<String, List<ImageResource>> illustrationCollector;

    private final Function<String, List<ImageResource>> diagramCollector;

    private final Function<String, List<ImageResource>> logoCollector;

    public ImageCollectorNode() {
        this(prompt -> Collections.emptyList(), 12);
    }

    public ImageCollectorNode(ImageCollectionService imageCollectionService, int imageSummaryLimit) {
        this.imageCollectionService = imageCollectionService;
        this.imageCollectionPlanService = null;
        this.imageSummaryLimit = imageSummaryLimit;
        this.contentCollector = null;
        this.illustrationCollector = null;
        this.diagramCollector = null;
        this.logoCollector = null;
    }

    public ImageCollectorNode(ImageCollectionPlanService imageCollectionPlanService,
                              int imageSummaryLimit,
                              Function<String, List<ImageResource>> contentCollector,
                              Function<String, List<ImageResource>> illustrationCollector,
                              Function<String, List<ImageResource>> diagramCollector,
                              Function<String, List<ImageResource>> logoCollector) {
        this.imageCollectionService = null;
        this.imageCollectionPlanService = imageCollectionPlanService;
        this.imageSummaryLimit = imageSummaryLimit;
        this.contentCollector = contentCollector;
        this.illustrationCollector = illustrationCollector;
        this.diagramCollector = diagramCollector;
        this.logoCollector = logoCollector;
    }

    public Map<String, Object> apply(AgentState state) {
        var ctx = WorkflowContext.fromState(state);
        log.info("[ImageCollectorNode] starting for appId={}", ctx.getAppId());
        ctx.advanceStep("image_collect");
        try {
            List<ImageResource> imageList = useParallelPlanMode()
                    ? collectImagesInParallel(ctx.getOriginalPrompt())
                    : imageCollectionService.collectImages(ctx.getOriginalPrompt());
            List<ImageResource> safeImageList = CollUtil.isEmpty(imageList) ? Collections.emptyList() : imageList;
            ctx.setImageList(safeImageList);
            ctx.setImageListStr(buildImageSummary(safeImageList));
        } catch (Exception e) {
            log.warn("[ImageCollectorNode] image collection failed, appId={}", ctx.getAppId(), e);
            ctx.setImageList(Collections.emptyList());
            ctx.setImageListStr("");
        }
        log.info("[ImageCollectorNode] completed, imageCount={}, imageListStr={}",
                ctx.getImageList().size(), ctx.getImageListStr());
        return ctx.toStateUpdate();
    }

    private String buildImageSummary(List<ImageResource> imageList) {
        if (CollUtil.isEmpty(imageList)) {
            return "";
        }
        return imageList.stream()
                .limit(imageSummaryLimit)
                .map(image -> StrUtil.format("[{}] {}", image.getCategory(), image.getDescription()))
                .collect(Collectors.joining("; "));
    }

    private boolean useParallelPlanMode() {
        return imageCollectionPlanService != null
                && contentCollector != null
                && illustrationCollector != null
                && diagramCollector != null
                && logoCollector != null;
    }

    private List<ImageResource> collectImagesInParallel(String originalPrompt) {
        ImageCollectionPlan plan = imageCollectionPlanService.buildPlan(originalPrompt);
        if (plan == null) {
            return Collections.emptyList();
        }
        CompletableFuture<List<ImageResource>> contentFuture = CompletableFuture.supplyAsync(() -> collectSafely(contentCollector, plan.getContentQuery()));
        CompletableFuture<List<ImageResource>> illustrationFuture = CompletableFuture.supplyAsync(() -> collectSafely(illustrationCollector, plan.getIllustrationQuery()));
        CompletableFuture<List<ImageResource>> diagramFuture = CompletableFuture.supplyAsync(() -> collectSafely(diagramCollector, plan.getDiagramQuery()));
        CompletableFuture<List<ImageResource>> logoFuture = CompletableFuture.supplyAsync(() -> collectSafely(logoCollector, plan.getLogoPrompt()));
        CompletableFuture.allOf(contentFuture, illustrationFuture, diagramFuture, logoFuture).join();
        List<ImageResource> results = new ArrayList<>();
        results.addAll(contentFuture.join());
        results.addAll(illustrationFuture.join());
        results.addAll(diagramFuture.join());
        results.addAll(logoFuture.join());
        return results;
    }

    private List<ImageResource> collectSafely(Function<String, List<ImageResource>> collector, String query) {
        if (collector == null || StrUtil.isBlank(query)) {
            return Collections.emptyList();
        }
        try {
            List<ImageResource> result = collector.apply(query);
            return CollUtil.isEmpty(result) ? Collections.emptyList() : result;
        } catch (Exception e) {
            log.warn("[ImageCollectorNode] parallel collector failed, query={}", query, e);
            return Collections.emptyList();
        }
    }
}
