package com.adcage.acaicodefree.core.saver;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;

public class SingleAbstractCodeFileSaver extends AbstractCodeFileSaver<SingleCodeResult> {
    /**
     * 获取代码类型,当前类为单文件类型
     *
     * @return
     */
    @Override
    public CodeGenTypeEnum getCodeType() {
        return CodeGenTypeEnum.SINGLE_FILE;
    }

    @Override
    protected void saveFile(String dirPath, SingleCodeResult result) {
        writeToFile(dirPath, "index.html", result.getHtmlCode());
    }

    @Override
    protected void validateInput(SingleCodeResult result) {
        super.validateInput(result);
        if (StrUtil.isBlank(result.getHtmlCode())) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "HTML代码不能为空");
        }
    }
}
