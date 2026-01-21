package com.adcage.acaicodefree.core.saver;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;

import java.io.File;
import java.nio.charset.StandardCharsets;

/**
 * 代码文件保存模板(模板方法)
 * @author adcage
 * @description AbstractCodeFileSaver
 */
public abstract class AbstractCodeFileSaver<T> {

    // 保存文件的根目录
    private static final String FILE_SAVE_ROOT_DIR = System.getProperty("user.dir") + File.separator + "temp" + File.separator + "code_output";

    /**
     * 保存文件模板流程
     *
     * @param result 类型结果(多文件,单文件)
     * @return 文件生成的目录
     */
    public final File saveCode(T result) {
        // 1.验证输入
        validateInput(result);
        // 2.构建唯一目录
        String dirPath = buildUniqueDirPath();
        // 3.保存文件
        saveFile(dirPath, result);
        // 4.返回结果
        return new File(dirPath);
    }

    /**
     * 验证输入参数,可由子类覆盖
     *
     * @param result
     */
    protected void validateInput(T result) {
        if (result == null) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "输入参数不能为空");
        }
    }

    /**
     * 保存单个文件
     *
     * @param dirPath  文件保存的目录
     * @param fileName 文件名
     * @param content  文件内容
     */
    public final void writeToFile(String dirPath, String fileName, String content) {
        if (StrUtil.isNotBlank(content)) {
            String filePath = dirPath + File.separator + fileName;
            // 不需要额外检测文件夹是否存在，hutool底层有一个touch方法会自动创建(如果没有的话)
            FileUtil.writeString(content, filePath, StandardCharsets.UTF_8);
        }
    }

    /**
     * 构建文件的唯一路径(temp/code_output/bizType_雪花ID)
     * 使用雪花算法生成唯一ID
     *
     * @return 唯一路径
     */
    private String buildUniqueDirPath() {
        String codeType = getCodeType().getValue();
        String uniqueDirName = StrUtil.format("{}_{}", codeType, IdUtil.getSnowflakeNextIdStr());
        String dirPath = FILE_SAVE_ROOT_DIR + File.separator + uniqueDirName;
        FileUtil.mkdir(dirPath);
        return dirPath;
    }

    public abstract CodeGenTypeEnum getCodeType();

    /**
     * 保存单个文件
     *
     * @param dirPath 文件保存的目录
     * @param result  文件内容
     */
    protected abstract void saveFile(String dirPath, T result);
}
