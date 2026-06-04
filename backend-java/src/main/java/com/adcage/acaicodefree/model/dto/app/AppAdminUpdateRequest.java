package com.adcage.acaicodefree.model.dto.app;

import lombok.Data;

import java.io.Serializable;

/**
 * 更新应用请求（管理员）
 * 
 * @author adcage
 */
@Data
public class AppAdminUpdateRequest implements Serializable {

    /**
     * 应用id
     */
    private Long id;

    /**
     * 应用名称
     */
    private String appName;

    /**
     * 应用封面
     */
    private String cover;

    /**
     * 优先级
     */
    private Integer priority;

    private static final long serialVersionUID = 1L;
}
