package com.adcage.acaicodefree.model.dto.modelconfig;

import com.adcage.acaicodefree.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

@EqualsAndHashCode(callSuper = true)
@Data
public class ModelConfigQueryRequest extends PageRequest implements Serializable {

    private String provider;

    private String modelName;

    private Integer enabled;

    private static final long serialVersionUID = 1L;
}
