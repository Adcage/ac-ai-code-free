package com.adcage.acaicodefree.core.saver;

import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;

/**
 * 多文件保存类
 *
 * @author adcage
 * @description MultiCodeFileSaver
 */
public class MultiCodeFileSaver extends AbstractCodeFileSaver<MultiFileCodeResult> {

    @Override
    public CodeGenTypeEnum getCodeType() {
        return CodeGenTypeEnum.MULTI_FILE;
    }

    @Override
    protected void saveFile(String dirPath, MultiFileCodeResult result) {
        writeToFile(dirPath, "index.html", result.getHtmlCode());
        writeToFile(dirPath, "style.css", result.getCssCode());
        writeToFile(dirPath, "script.js", result.getJsCode());
    }

    @Override
    protected void validateInput(MultiFileCodeResult result) {
        super.validateInput(result);
        if (StrUtil.isBlank(result.getHtmlCode())) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "HTML代码不能为空");
        }
    }
}