package com.adcage.acaicodefree.workflow.controller;

import com.adcage.acaicodefree.workflow.service.WorkflowCodeGeneratorService;
import jakarta.annotation.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/workflow/sse")
public class WorkflowSseController {

    @Resource
    private WorkflowCodeGeneratorService workflowCodeGeneratorService;

    @GetMapping(value = "/execute", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> execute(@RequestParam Long appId, @RequestParam String message) {
        return workflowCodeGeneratorService.executeWorkflowEventFlux(appId, message)
                .map(event -> ServerSentEvent.<String>builder()
                        .event(event.event())
                        .data(event.data())
                        .build());
    }
}
