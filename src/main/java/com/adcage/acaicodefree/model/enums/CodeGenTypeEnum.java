package com.adcage.acaicodefree.model.enums;

import cn.hutool.core.util.ObjUtil;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 代码生成类型枚举
 * @author adcage
 * @description CodeGenTypeEnum
 */
@Getter
@AllArgsConstructor
public enum CodeGenTypeEnum {
    HTML("HTML", "html"),
    MULTI_FILE("多文件代码模式", "multi-file");

    private final String text;
    private final String value;

    /**
     * 根据 value 获取枚举
     *
     * @param value 枚举值的value
     * @return 枚举值
     */
    public static CodeGenTypeEnum getEnumByValue(String value) {
        if (ObjUtil.isEmpty(value)) {
            return null;
        }
        for (CodeGenTypeEnum anEnum : CodeGenTypeEnum.values()) {
            if (anEnum.value.equals(value)) {
                return anEnum;
            }
        }
        return null;
    }

}
