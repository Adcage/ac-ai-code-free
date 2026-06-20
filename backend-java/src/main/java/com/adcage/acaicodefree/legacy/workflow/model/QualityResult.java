package com.adcage.acaicodefree.legacy.workflow.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QualityResult implements Serializable {

    private Boolean isValid;

    @Builder.Default
    private List<String> errors = new ArrayList<>();

    @Builder.Default
    private List<String> suggestions = new ArrayList<>();

    public static QualityResult valid() {
        return QualityResult.builder().isValid(true).build();
    }

    public static QualityResult invalid(List<String> errors) {
        return QualityResult.builder().isValid(false).errors(errors).build();
    }

    public static QualityResult invalidWithSuggestions(List<String> errors, List<String> suggestions) {
        return QualityResult.builder().isValid(false).errors(errors).suggestions(suggestions).build();
    }
}
