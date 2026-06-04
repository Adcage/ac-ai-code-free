package com.adcage.acaicodefree.core.parser;

public interface CodePaser<T> {
    /**
     *
     * @param codeContent
     * @return
     */
    T parseCode(String codeContent) ;
}
