package com.adcage.acaicodefree.grpc.server;

import com.adcage.acaicodefree.grpc.common.CodeGenType;
import com.adcage.acaicodefree.grpc.tool.*;
import com.adcage.acaicodefree.service.FileOperationService;
import io.grpc.stub.StreamObserver;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;
import jakarta.annotation.Resource;

@Slf4j
@GrpcService
public class GrpcToolService extends ToolServiceGrpc.ToolServiceImplBase {

    @Resource
    private FileOperationService fileOperationService;

    @Override
    public void readFile(ReadFileRequest request, StreamObserver<ReadFileResponse> responseObserver) {
        try {
            String content = fileOperationService.readFile(
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType()),
                    request.getRelativePath()
            );
            responseObserver.onNext(ReadFileResponse.newBuilder().setContent(content).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC readFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void writeFile(WriteFileRequest request, StreamObserver<WriteFileResponse> responseObserver) {
        try {
            String message = fileOperationService.writeFile(
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType()),
                    request.getRelativePath(),
                    request.getContent()
            );
            responseObserver.onNext(WriteFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC writeFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void modifyFile(ModifyFileRequest request, StreamObserver<ModifyFileResponse> responseObserver) {
        try {
            String message = fileOperationService.modifyFile(
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType()),
                    request.getRelativePath(),
                    request.getOldContent(),
                    request.getNewContent()
            );
            responseObserver.onNext(ModifyFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC modifyFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void deleteFile(DeleteFileRequest request, StreamObserver<DeleteFileResponse> responseObserver) {
        try {
            String message = fileOperationService.deleteFile(
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType()),
                    request.getRelativePath()
            );
            responseObserver.onNext(DeleteFileResponse.newBuilder().setMessage(message).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC deleteFile failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public void readDir(ReadDirRequest request, StreamObserver<ReadDirResponse> responseObserver) {
        try {
            String entries = fileOperationService.readDir(
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType()),
                    request.getRelativePath()
            );
            responseObserver.onNext(ReadDirResponse.newBuilder().setEntries(entries).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("gRPC readDir failed", e);
            responseObserver.onError(io.grpc.Status.INTERNAL
                    .withDescription(e.getMessage()).asRuntimeException());
        }
    }

    @Override
    public StreamObserver<WriteFileRequest> streamWriteFiles(StreamObserver<BatchWriteResponse> responseObserver) {
        int[] counts = {0, 0};
        return new StreamObserver<>() {
            @Override
            public void onNext(WriteFileRequest request) {
                try {
                    String message = fileOperationService.writeFile(
                            request.getAppId(),
                            mapCodeGenType(request.getCodeGenType()),
                            request.getRelativePath(),
                            request.getContent()
                    );
                    counts[0]++;
                } catch (Exception e) {
                    counts[1]++;
                    log.warn("streamWriteFiles item failed", e);
                }
            }

            @Override
            public void onError(Throwable t) {
                log.error("streamWriteFiles client error", t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(BatchWriteResponse.newBuilder()
                        .setSuccessCount(counts[0])
                        .setFailureCount(counts[1])
                        .build());
                responseObserver.onCompleted();
            }
        };
    }

    private String mapCodeGenType(CodeGenType grpcType) {
        return switch (grpcType) {
            case SINGLE_FILE -> "single_file";
            case MULTI_FILE -> "multi-file";
            case VUE_PROJECT -> "vue_project";
            default -> "vue_project";
        };
    }
}
