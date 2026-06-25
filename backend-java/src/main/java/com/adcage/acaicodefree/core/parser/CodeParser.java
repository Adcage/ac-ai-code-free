package com.adcage.acaicodefree.core.parser;

public interface CodeParser<T> {
    /**
     *
     * @param codeContent
     * @return
     */
    T parseCode(String codeContent) ;
}
