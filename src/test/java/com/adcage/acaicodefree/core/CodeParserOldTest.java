package com.adcage.acaicodefree.core;

import com.adcage.acaicodefree.ai.model.SingleCodeResult;
import com.adcage.acaicodefree.ai.model.MultiFileCodeResult;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.exception.BusinessException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class CodeParserTest {

    @Test
    void testParseSingleCode_WithValidHtml() {
        String content = "```html\n<div>Test</div>\n```";
        SingleCodeResult result = CodeParser.parseSingleCode(content);
        assertNotNull(result);
        System.out.println(result.getHtmlCode());
        assertEquals("<div>Test</div>", result.getHtmlCode());
    }

    @Test
    void testParseSingleCode_WithCaseInsensitiveHtml() {
        String content = "```SINGLE_FILE\n<div>Test</div>\n```";
        SingleCodeResult result = CodeParser.parseSingleCode(content);
        assertNotNull(result);
        assertEquals("<div>Test</div>", result.getHtmlCode());
    }

    @Test
    void testParseSingleCode_WithNoHtml() {
        String content = "Some text without SINGLE_FILE code blocks";
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            CodeParser.parseSingleCode(content);
        });
        assertEquals(ErrorCode.NOT_FOUND_ERROR.getCode(), exception.getCode());
        assertEquals("未找到HTML代码", exception.getMessage());
    }

    @Test
    void testParseSingleCode_WithEmptyHtml() {
        String content = "```html\n\n```";
        BusinessException exception = assertThrows(BusinessException.class, () -> {
            CodeParser.parseSingleCode(content);
        });
        assertEquals(ErrorCode.NOT_FOUND_ERROR.getCode(), exception.getCode());
    }

    @Test
    void testExtractMutiFileCode_WithAllCodeTypes() {
        String content = "```html\n<div>Test</div>\n```\n```css\nbody { color: red; }\n```\n```js\nconsole.log('test');\n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("<div>Test</div>", result.getHtmlCode());
        assertEquals("body { color: red; }", result.getCssCode());
        assertEquals("console.log('test');", result.getJsCode());
    }

    @Test
    void testExtractMutiFileCode_WithJavaScript() {
        String content = "```javascript\nconsole.log('test');\n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("console.log('test');", result.getJsCode());
    }

    @Test
    void testExtractMutiFileCode_WithEmptyContent() {
        MultiFileCodeResult result = CodeParser.extractMutiFileCode("");
        assertNull(result);
    }

    @Test
    void testExtractMutiFileCode_WithNullContent() {
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(null);
        assertNull(result);
    }

    @Test
    void testExtractMutiFileCode_WithPartialCode() {
        String content = "```html\n<div>Test</div>\n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("<div>Test</div>", result.getHtmlCode());
        assertNull(result.getCssCode());
        assertNull(result.getJsCode());
    }

    @Test
    void testExtractMutiFileCode_WithMultipleMatches() {
        String content = "```html\n<div>First</div>\n```\n```html\n<div>Second</div>\n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("<div>First</div>", result.getHtmlCode());
    }

    @Test
    void testExtractMutiFileCode_WithWhitespaceInCodeBlocks() {
        String content = "```html\n  <div>Test</div>  \n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("<div>Test</div>", result.getHtmlCode());
    }

    @Test
    void testExtractMutiFileCode_WithMixedCase() {
        String content = "```SINGLE_FILE\n<div>Test</div>\n```\n```CSS\nbody { color: red; }\n```\n```JavaScript\nconsole.log('test');\n```";
        MultiFileCodeResult result = CodeParser.extractMutiFileCode(content);
        assertNotNull(result);
        assertEquals("<div>Test</div>", result.getHtmlCode());
        assertEquals("body { color: red; }", result.getCssCode());
        assertEquals("console.log('test');", result.getJsCode());
    }
}
