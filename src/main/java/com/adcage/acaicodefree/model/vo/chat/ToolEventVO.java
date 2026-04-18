package com.adcage.acaicodefree.model.vo.chat;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

/**
 * 工具调用事件视图
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ToolEventVO implements Serializable {

    private String type;

    private String text;

    private static final long serialVersionUID = 1L;
}
