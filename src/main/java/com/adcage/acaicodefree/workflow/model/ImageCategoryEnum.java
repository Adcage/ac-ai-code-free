package com.adcage.acaicodefree.workflow.model;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum ImageCategoryEnum {
    CONTENT("内容图片", "content"),
    ILLUSTRATION("插画", "illustration"),
    ARCHITECTURE("架构图", "architecture"),
    LOGO("Logo", "logo");

    private final String text;
    private final String value;

    public static ImageCategoryEnum getEnumByValue(String value) {
        if (value == null) {
            return null;
        }
        for (ImageCategoryEnum e : values()) {
            if (e.value.equals(value)) {
                return e;
            }
        }
        return null;
    }
}
