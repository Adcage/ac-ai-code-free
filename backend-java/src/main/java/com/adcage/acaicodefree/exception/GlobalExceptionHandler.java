package com.adcage.acaicodefree.exception;

import com.adcage.acaicodefree.common.BaseResponse;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.common.ResultUtils;
import io.swagger.v3.oas.annotations.Hidden;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 * @author adcage
 */
@Hidden //添加该注解避免与swagger-ui冲突
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public BaseResponse<?> businessExceptionHandler(BusinessException e) {
        log.warn("BusinessException", e);
        return ResultUtils.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(RuntimeException.class)
    public BaseResponse<?> runtimeExceptionHandler(RuntimeException e) {
        log.error("RuntimeException", e);
        return ResultUtils.error(ErrorCode.SYSTEM_ERROR, "系统错误");
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public BaseResponse<?> methodArgumentTypeMismatchExceptionHandler(MethodArgumentTypeMismatchException e) {
        String parameterName = e.getName();
        Object invalidValue = e.getValue();
        log.warn("MethodArgumentTypeMismatch, parameter={}, value={}", parameterName, invalidValue, e);
        return ResultUtils.error(ErrorCode.PARAMS_ERROR,
                String.format("参数 %s 类型错误，当前值：%s", parameterName, String.valueOf(invalidValue)));
    }
}
