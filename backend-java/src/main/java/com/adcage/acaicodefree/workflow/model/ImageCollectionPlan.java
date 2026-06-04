package com.adcage.acaicodefree.workflow.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ImageCollectionPlan implements Serializable {

    private String contentQuery;

    private String illustrationQuery;

    private String diagramQuery;

    private String logoPrompt;
}
