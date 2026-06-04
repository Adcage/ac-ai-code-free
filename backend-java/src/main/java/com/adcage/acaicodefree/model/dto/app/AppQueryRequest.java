package com.adcage.acaicodefree.model.dto.app;

import com.adcage.acaicodefree.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 查询应用请求
 * 
 * @author adcage
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class AppQueryRequest extends PageRequest implements Serializable {

    /**
     * id
     */
    private Long id;

    /**
     * 应用名称
     */
    private String appName;

    /**
     * 初始化提示词
     */
    private String initPrompt;

    /**
     * 代码生成类型（枚举）
     */
    private String codeGenType;

    /**
     * 部署标识
     */
    private String deployKey;

    /**
     * 优先级
     */
    private Integer priority;

    /**
     * 创建用户id
     */
    private Long userId;

    /**
     * 创建人
     */
    private String userName;

    /**
     * 是否仅查询精选（优先级大于0）
     */
    private Boolean onlyFeatured;

    private static final long serialVersionUID = 1L;
}
