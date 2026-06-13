package com.adcage.acaicodefree.legacy.workflow.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

@Configuration
public class WorkflowThreadPoolConfig {

    @Bean(destroyMethod = "shutdown")
    public ExecutorService workflowImageCollectExecutor() {
        AtomicInteger threadIndex = new AtomicInteger();
        return Executors.newFixedThreadPool(4, runnable -> {
            Thread thread = new Thread(runnable);
            thread.setName("Parallel-Image-Collect-" + threadIndex.getAndIncrement());
            return thread;
        });
    }
}
