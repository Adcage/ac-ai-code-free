package com.adcage.acaicodefree.model.dto.app;

import lombok.Data;

import java.io.Serializable;

/**
 * 编辑应用请求（用户编辑自己的应用）
 * 
 * @author adcage
 */
@Data
public class AppEditRequest implements Serializable {

    /**
     * 应用id
     */
    private Long id;

    /**
     * 应用名称
     */
    private String appName;

    private static final long serialVersionUID = 1L;
}
