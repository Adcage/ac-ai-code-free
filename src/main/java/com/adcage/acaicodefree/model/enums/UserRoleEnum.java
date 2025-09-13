package com.adcage.acaicodefree.model.enums;

import cn.hutool.core.util.ObjUtil;
import lombok.Getter;

/**
 * 用户角色枚举
 */
@Getter
public enum UserRoleEnum {

    USER("用户", "user",1),
    ADMIN("管理员", "admin",999),
    VIP("会员", "vip",2);

    private final String text;

    private final String value;

    private final int level;

    UserRoleEnum(String text, String value, int level) {
        this.text = text;
        this.value = value;
        this.level = level;
    }

    /**
     * 根据 value 获取枚举
     *
     * @param value 枚举值的value
     * @return 枚举值
     */
    public static UserRoleEnum getEnumByValue(String value) {
        if (ObjUtil.isEmpty(value)) {
            return null;
        }
        for (UserRoleEnum anEnum : UserRoleEnum.values()) {
            if (anEnum.value.equals(value)) {
                return anEnum;
            }
        }
        return null;
    }
}
