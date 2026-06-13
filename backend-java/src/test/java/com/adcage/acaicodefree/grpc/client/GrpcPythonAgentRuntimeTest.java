package com.adcage.acaicodefree.grpc.client;

import com.adcage.acaicodefree.grpc.codegen.CodeGenerationServiceGrpc;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertSame;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class GrpcPythonAgentRuntimeTest {

    @Test
    void prepareStreamGenerateStubShouldWaitForReadyWithDeadline() {
        GrpcPythonAgentRuntime runtime = new GrpcPythonAgentRuntime();
        CodeGenerationServiceGrpc.CodeGenerationServiceStub stub = mock(CodeGenerationServiceGrpc.CodeGenerationServiceStub.class);
        ReflectionTestUtils.setField(runtime, "codeGenServiceStub", stub);
        ReflectionTestUtils.setField(runtime, "streamDeadlineSeconds", 300);
        when(stub.withWaitForReady()).thenReturn(stub);
        when(stub.withDeadlineAfter(300, TimeUnit.SECONDS)).thenReturn(stub);

        CodeGenerationServiceGrpc.CodeGenerationServiceStub prepared = runtime.prepareStreamGenerateStub();

        assertSame(stub, prepared);
        var inOrder = inOrder(stub);
        inOrder.verify(stub).withWaitForReady();
        inOrder.verify(stub).withDeadlineAfter(300, TimeUnit.SECONDS);
    }
}
