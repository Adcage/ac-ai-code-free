package com.adcage.acaicodefree.core;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;

import java.io.File;
import java.nio.charset.StandardCharsets;

/**
 * 文件保存类
 *
 * @author adcage
 * @description CodeFileSaver
 */
public class CodeFileSaver {

    // 保存文件的根目录
    private static final String FILE_SAVE_ROOT_DIR = System.getProperty("user.dir") + File.separator + "temp" + File.separator + "code_output";

    /**
     * 生成唯一文件保存的目录,并且保存 SINGLE_FILE 网页代码
     *
     * @param htmlCode html代码
     */
    public static File saveHtmlCode(SingleCodeResult htmlCode) {
        String uniqueFilePath = buildUniqueDirPath(CodeGenTypeEnum.SINGLE_FILE.getValue());
        saveFile(uniqueFilePath, "index.html", htmlCode.getHtmlCode());
        return new File(uniqueFilePath);
    }


    /**
     * 生成唯一文件保存的目录,保存文件存多文件代码
     *
     * @param multiFileCode 多文件代码类对象
     */
    public static File saveMutiFileCode(MultiFileCodeResult multiFileCode) {
        String uniqueFilePath = buildUniqueDirPath(CodeGenTypeEnum.MULTI_FILE.getValue());
        saveFile(uniqueFilePath, "index.html", multiFileCode.getHtmlCode());
        saveFile(uniqueFilePath, "style.css", multiFileCode.getCssCode());
        saveFile(uniqueFilePath, "script.js", multiFileCode.getJsCode());
        return new File(uniqueFilePath);
    }

    /**
     * 构建文件的唯一路径(temp/code_output/bizType_雪花ID)
     * 使用雪花算法生成唯一ID
     *
     * @param bitType 业务类型
     * @return 唯一路径
     */
    private static String buildUniqueDirPath(String bitType) {
        String uniqueDirName = StrUtil.format("{}_{}", bitType, IdUtil.getSnowflakeNextIdStr());
        String dirPath = FILE_SAVE_ROOT_DIR + File.separator + uniqueDirName;
        FileUtil.mkdir(dirPath);
        return dirPath;
    }

    /**
     * 保存单个文件
     *
     * @param dirPath  文件保存的目录
     * @param fileName 文件名
     * @param content  文件内容
     */
    private static void saveFile(String dirPath, String fileName, String content) {
        String filePath = dirPath + File.separator + fileName;
        // 不需要额外检测文件夹是否存在，hutool底层有一个touch方法会自动创建(如果没有的话)
        FileUtil.writeString(content, filePath, StandardCharsets.UTF_8);
    }

}

