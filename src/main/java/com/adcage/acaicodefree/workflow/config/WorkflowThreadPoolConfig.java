package com.adcage.acaicodefree.workflow.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Configuration
public class WorkflowThreadPoolConfig {

    @Bean(destroyMethod = "shutdown")
    public ExecutorService workflowImageCollectExecutor() {
        return Executors.newFixedThreadPool(4, Thread.ofPlatform().name("Parallel-Image-Collect-", 0).factory());
    }
}
