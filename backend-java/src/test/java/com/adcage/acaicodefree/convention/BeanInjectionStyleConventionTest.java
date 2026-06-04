package com.adcage.acaicodefree.convention;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Controller;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RestController;

import java.lang.annotation.Annotation;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

class BeanInjectionStyleConventionTest {

    private static final String BASE_PACKAGE = "com.adcage.acaicodefree";

    @Test
    void beanClassesShouldNotUseParameterizedConstructors() throws ClassNotFoundException {
        Set<String> violations = new TreeSet<>();
        for (Class<? extends Annotation> annotationType : beanAnnotations()) {
            ClassPathScanningCandidateComponentProvider scanner =
                    new ClassPathScanningCandidateComponentProvider(false);
            scanner.addIncludeFilter(new AnnotationTypeFilter(annotationType));
            scanner.findCandidateComponents(BASE_PACKAGE).forEach(beanDefinition -> {
                try {
                    Class<?> beanClass = Class.forName(beanDefinition.getBeanClassName());
                    if (beanClass.isInterface() || java.lang.reflect.Modifier.isAbstract(beanClass.getModifiers())) {
                        return;
                    }
                    for (Constructor<?> constructor : beanClass.getDeclaredConstructors()) {
                        if (constructor.getParameterCount() > 0) {
                            violations.add(beanClass.getName() + " -> " + constructor);
                        }
                    }
                } catch (ClassNotFoundException e) {
                    throw new RuntimeException(e);
                }
            });
        }
        Assertions.assertTrue(violations.isEmpty(),
                () -> "以下 Spring Bean 存在参数化构造函数，请改为 @Resource / 字段 @Value 注入:\n" + String.join("\n", violations));
    }

    private List<Class<? extends Annotation>> beanAnnotations() {
        List<Class<? extends Annotation>> result = new ArrayList<>();
        result.add(Service.class);
        result.add(Component.class);
        result.add(Controller.class);
        result.add(RestController.class);
        result.add(org.springframework.context.annotation.Configuration.class);
        return result;
    }
}
