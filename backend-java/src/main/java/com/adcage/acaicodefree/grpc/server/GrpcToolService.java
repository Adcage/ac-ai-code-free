package com.adcage.acaicodefree.grpc.server;

import com.adcage.acaicodefree.grpc.common.CodeGenType;
import com.adcage.acaicodefree.grpc.tool.*;
import com.adcage.acaicodefree.ai.tools.FileReadTool;
import com.adcage.acaicodefree.ai.tools.FileWriteTool;
import com.adcage.acaicodefree.ai.tools.FileModifyTool;
import com.adcage.acaicodefree.ai.tools.FileDeleteTool;
import com.adcage.acaicodefree.ai.tools.FileDirReadTool;
import io.grpc.stub.StreamObserver;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;
import jakarta.annotation.Resource;

@Slf4j
@GrpcService
public class GrpcToolService extends ToolServiceGrpc.ToolServiceImplBase {

    @Resource
    private FileReadTool fileReadTool;
    @Resource
    private FileWriteTool fileWriteTool;
    @Resource
    private FileModifyTool fileModifyTool;
    @Resource
    private FileDeleteTool fileDeleteTool;
    @Resource
    private FileDirReadTool fileDirReadTool;

    @Override
    public void readFile(ReadFileRequest request, StreamObserver<ReadFileResponse> responseObserver) {
        try {
            String content = fileReadTool.readFile(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
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
            String message = fileWriteTool.writeFile(
                    request.getRelativePath(),
                    request.getContent(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
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
            String message = fileModifyTool.modifyFile(
                    request.getRelativePath(),
                    request.getOldContent(),
                    request.getNewContent(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
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
            String message = fileDeleteTool.deleteFile(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
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
            String entries = fileDirReadTool.readDir(
                    request.getRelativePath(),
                    request.getAppId(),
                    mapCodeGenType(request.getCodeGenType())
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
                    String message = fileWriteTool.writeFile(
                            request.getRelativePath(),
                            request.getContent(),
                            request.getAppId(),
                            mapCodeGenType(request.getCodeGenType())
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
