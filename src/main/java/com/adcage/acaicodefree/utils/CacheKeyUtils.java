package com.adcage.acaicodefree.utils;

import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.json.JSONUtil;

public class CacheKeyUtils {

    public static String generateKey(String prefix, Object... params) {
        String json = JSONUtil.toJsonStr(params);
        String hash = DigestUtil.md5Hex(json);
        return prefix + ":" + hash;
    }
}
