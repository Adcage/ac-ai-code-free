package com.adcage.acaicodefree.grpc.server;

import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import net.devh.boot.grpc.server.interceptor.GrpcGlobalServerInterceptor;
import org.springframework.beans.factory.annotation.Value;

@GrpcGlobalServerInterceptor
public class GrpcInternalAuthInterceptor implements ServerInterceptor {

    private static final Metadata.Key<String> INTERNAL_SECRET_KEY =
            Metadata.Key.of("x-internal-secret", Metadata.ASCII_STRING_MARSHALLER);

    @Value("${agent.runtime-internal-secret:}")
    private String internalSecret;

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers,
            ServerCallHandler<ReqT, RespT> next) {
        if (internalSecret != null && !internalSecret.isBlank()) {
            String provided = headers.get(INTERNAL_SECRET_KEY);
            if (!internalSecret.equals(provided)) {
                call.close(io.grpc.Status.UNAUTHENTICATED
                        .withDescription("Invalid internal secret"), headers);
                return new ServerCall.Listener<>() {};
            }
        }
        return next.startCall(call, headers);
    }
}
