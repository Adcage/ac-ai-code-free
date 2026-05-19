package com.adcage.acaicodefree.ratelimit.annotation;

import com.adcage.acaicodefree.ratelimit.enums.RateLimitType;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimit {
    RateLimitType type() default RateLimitType.USER;

    int rate() default 5;

    int intervalSeconds() default 60;

    String message() default "请求过于频繁，请稍后再试";
}
