package com.adcage.acaicodefree.core.parser;

import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SingleFileParser implements CodePaser<SingleCodeResult>{

    /**
     * SINGLE_FILE 代码块匹配模式 (```html ... ```)
     */
    private static final Pattern HTML_CODE_PATTERN = Pattern.compile("```html\\s*([\\s\\S]*?)```", Pattern.CASE_INSENSITIVE);


    /**
     * 解析单文件代码（仅提取 SINGLE_FILE）
     *
     * @param content AI 生成的原始内容
     * @return 包含 SINGLE_FILE 代码的解析结果
     * @throws BusinessException 如果未找到 SINGLE_FILE 代码则抛出异常
     */
    @Override
    public SingleCodeResult parseCode(String content) {
        SingleCodeResult result = new SingleCodeResult();
        // 提取 SINGLE_FILE 代码
        String htmlCode = processCode(extractHtmlCode(content));
        if (htmlCode != null) {
            result.setHtmlCode(htmlCode);
        } else {
            throw new BusinessException(ErrorCode.NOT_FOUND_ERROR, "未找到HTML代码");
        }
        return result;
    }

    /**
     * 处理代码字符串：trim 并判断是否为空
     *
     * @param code 提取的代码
     * @return 处理后的代码，如果为空则返回 null
     */
    private static String processCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            return null;
        }
        return code.trim();
    }

    /**
     * 从文本中提取 SINGLE_FILE 代码块内容
     *
     * @param content AI 生成的原始内容
     * @return 匹配到的代码内容，未匹配到则返回 null
     */
    private static String extractHtmlCode(String content) {
        Matcher matcher = HTML_CODE_PATTERN.matcher(content);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }

}
