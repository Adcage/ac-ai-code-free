package com.adcage.acaicodefree.service;

import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.model.vo.modelconfig.ModelConfigVO;
import com.mybatisflex.core.service.IService;

import java.util.List;

public interface ModelConfigService extends IService<ModelConfig> {

    void validModelConfig(ModelConfig modelConfig, boolean add);

    ModelConfigVO getModelConfigVO(ModelConfig modelConfig);

    List<ModelConfigVO> getModelConfigVOList(List<ModelConfig> modelConfigList);

    void incrementConfigVersion(Long id);
}
