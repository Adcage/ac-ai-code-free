package com.adcage.acaicodefree.model.enums;

import cn.hutool.core.util.ObjUtil;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 浏览器类型枚举
 * @author adcage
 */
@Getter
@AllArgsConstructor
public enum BrowserTypeEnum {

    CHROME("Chrome 浏览器", "chrome"),
    EDGE("Microsoft Edge 浏览器", "edge"),
    FIREFOX("Firefox 浏览器", "firefox");

    private final String text;
    private final String value;

    /**
     * 根据 value 获取枚举
     *
     * @param value 枚举值的 value
     * @return 枚举值
     */
    public static BrowserTypeEnum getEnumByValue(String value) {
        if (ObjUtil.isEmpty(value)) {
            return CHROME;
        }
        for (BrowserTypeEnum anEnum : BrowserTypeEnum.values()) {
            if (anEnum.value.equals(value)) {
                return anEnum;
            }
        }
        return CHROME;
    }
}
