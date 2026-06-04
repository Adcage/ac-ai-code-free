package com.adcage.acaicodefree.ratelimit.aspect;

import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.ratelimit.annotation.RateLimit;
import com.adcage.acaicodefree.ratelimit.enums.RateLimitType;
import com.adcage.acaicodefree.service.UserService;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.redisson.api.RRateLimiter;
import org.redisson.api.RateIntervalUnit;
import org.redisson.api.RateType;
import org.redisson.api.RedissonClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Aspect
@Component
@ConditionalOnProperty(name = "app.redisson.enabled", havingValue = "true", matchIfMissing = true)
public class RateLimitAspect {

    private static final Logger log = LoggerFactory.getLogger(RateLimitAspect.class);

    @Resource
    private RedissonClient redissonClient;

    @Resource
    private UserService userService;

    @Around("@annotation(rateLimit)")
    public Object around(ProceedingJoinPoint joinPoint, RateLimit rateLimit) throws Throwable {
        String key = buildRateLimitKey(joinPoint, rateLimit);
        RRateLimiter rateLimiter = redissonClient.getRateLimiter(key);
        rateLimiter.trySetRate(RateType.OVERALL, rateLimit.rate(), rateLimit.intervalSeconds(), RateIntervalUnit.SECONDS);
        if (!rateLimiter.tryAcquire()) {
            log.warn("限流触发, key={}", key);
            throw new BusinessException(ErrorCode.TOO_MANY_REQUESTS, rateLimit.message());
        }
        return joinPoint.proceed();
    }

    private String buildRateLimitKey(ProceedingJoinPoint joinPoint, RateLimit rateLimit) {
        String methodName = joinPoint.getSignature().getDeclaringTypeName() + "." + joinPoint.getSignature().getName();
        return switch (rateLimit.type()) {
            case API -> "rate_limit:api:" + methodName;
            case USER -> {
                Long userId = getCurrentUserId();
                yield userId != null
                        ? "rate_limit:user:" + userId
                        : "rate_limit:ip:" + getClientIp();
            }
            case IP -> "rate_limit:ip:" + getClientIp();
        };
    }

    private Long getCurrentUserId() {
        try {
            ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs == null) return null;
            HttpServletRequest request = attrs.getRequest();
            User loginUser = userService.getLoginUserPermitNull(request);
            return loginUser != null ? loginUser.getId() : null;
        } catch (Exception e) {
            return null;
        }
    }

    private String getClientIp() {
        ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attrs == null) return "unknown";
        HttpServletRequest request = attrs.getRequest();
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }
}
