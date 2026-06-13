package com.adcage.acaicodefree.convention;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Stream;

class JavaAiCoreConventionTest {

    private static final List<String> FORBIDDEN_AI_CORE_MARKERS = List.of(
            "dev.langchain4j.service.AiServices",
            "@SystemMessage",
            "@UserMessage"
    );

    private static final List<String> LEGACY_AI_PATH_PREFIXES = List.of(
            "com/adcage/acaicodefree/ai/",
            "com/adcage/acaicodefree/workflow/ai/"
    );

    private static final List<String> LEGACY_AI_FILES = List.of(
            "com/adcage/acaicodefree/core/AiCodeGeneratorFacade.java",
            "com/adcage/acaicodefree/core/memory/ChatMemoryLoader.java"
    );

    @Test
    void javaLangChainAiCoreShouldOnlyRemainInDeprecatedLegacyFiles() throws IOException {
        Path sourceRoot = Path.of("src/main/java");
        Set<String> violations = new TreeSet<>();

        try (Stream<Path> files = Files.walk(sourceRoot)) {
            files.filter(path -> path.toString().endsWith(".java"))
                    .forEach(path -> inspectFile(sourceRoot, path, violations));
        }

        Assertions.assertTrue(violations.isEmpty(),
                () -> "Java AI 核心只能保留在已标记 @Deprecated 的 legacy 文件中:\n" + String.join("\n", violations));
    }

    private void inspectFile(Path sourceRoot, Path path, Set<String> violations) {
        try {
            String content = Files.readString(path);
            boolean containsJavaAiCoreMarker = FORBIDDEN_AI_CORE_MARKERS.stream().anyMatch(content::contains);
            if (!containsJavaAiCoreMarker) {
                return;
            }
            String relativePath = sourceRoot.relativize(path).toString().replace('\\', '/');
            if (!isLegacyAiFile(relativePath)) {
                violations.add(relativePath + " -> contains Java AI core marker outside legacy area");
                return;
            }
            if (!content.contains("@Deprecated")) {
                violations.add(relativePath + " -> legacy Java AI file must be marked @Deprecated");
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private boolean isLegacyAiFile(String relativePath) {
        return LEGACY_AI_PATH_PREFIXES.stream().anyMatch(relativePath::startsWith)
                || LEGACY_AI_FILES.contains(relativePath);
    }
}
