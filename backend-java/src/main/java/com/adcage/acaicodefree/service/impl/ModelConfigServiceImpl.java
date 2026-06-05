package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.mapper.ModelConfigMapper;
import com.adcage.acaicodefree.model.entity.ModelConfig;
import com.adcage.acaicodefree.model.vo.modelconfig.ModelConfigVO;
import com.adcage.acaicodefree.service.ModelConfigEventPublisher;
import com.adcage.acaicodefree.service.ModelConfigService;
import com.mybatisflex.spring.service.impl.ServiceImpl;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ModelConfigServiceImpl extends ServiceImpl<ModelConfigMapper, ModelConfig> implements ModelConfigService {

    @Resource
    private ModelConfigEventPublisher modelConfigEventPublisher;

    @Override
    public void validModelConfig(ModelConfig modelConfig, boolean add) {
        if (modelConfig == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR);
        }
        if (add) {
            ThrowUtils.throwIf(StrUtil.isBlank(modelConfig.getProvider()), ErrorCode.PARAMS_ERROR, "供应商不能为空");
            ThrowUtils.throwIf(StrUtil.isBlank(modelConfig.getModelName()), ErrorCode.PARAMS_ERROR, "模型名称不能为空");
            ThrowUtils.throwIf(StrUtil.isBlank(modelConfig.getBaseUrl()), ErrorCode.PARAMS_ERROR, "接口地址不能为空");
            ThrowUtils.throwIf(StrUtil.isBlank(modelConfig.getApiKeyCipher()), ErrorCode.PARAMS_ERROR, "API密钥不能为空");
        }
    }

    @Override
    public ModelConfigVO getModelConfigVO(ModelConfig modelConfig) {
        if (modelConfig == null) {
            return null;
        }
        ModelConfigVO modelConfigVO = new ModelConfigVO();
        BeanUtil.copyProperties(modelConfig, modelConfigVO);
        return modelConfigVO;
    }

    @Override
    public List<ModelConfigVO> getModelConfigVOList(List<ModelConfig> modelConfigList) {
        if (CollUtil.isEmpty(modelConfigList)) {
            return new ArrayList<>();
        }
        return modelConfigList.stream().map(this::getModelConfigVO).toList();
    }

    @Override
    public void incrementConfigVersion(Long id) {
        ModelConfig modelConfig = this.getById(id);
        ThrowUtils.throwIf(modelConfig == null, ErrorCode.NOT_FOUND_ERROR, "模型配置不存在");
        ModelConfig update = new ModelConfig();
        update.setId(id);
        update.setConfigVersion(modelConfig.getConfigVersion() + 1);
        boolean result = this.updateById(update);
        ThrowUtils.throwIf(!result, ErrorCode.OPERATION_ERROR, "更新配置版本失败");
        modelConfigEventPublisher.publishConfigUpdated(modelConfig);
    }
}
