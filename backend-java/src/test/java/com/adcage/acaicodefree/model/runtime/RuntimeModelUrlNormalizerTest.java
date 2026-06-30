package com.adcage.acaicodefree.model.runtime;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RuntimeModelUrlNormalizerTest {

    @Test
    void shouldKeepRootPath() {
        assertEquals(
                "https://api.example.com",
                RuntimeModelUrlNormalizer.normalize("https://api.example.com")
        );
    }

    @Test
    void shouldKeepVersionPath() {
        assertEquals(
                "https://api.example.com/v4",
                RuntimeModelUrlNormalizer.normalize("https://api.example.com/v4")
        );
    }

    @Test
    void shouldRemoveTrailingSlash() {
        assertEquals(
                "https://api.example.com/v1",
                RuntimeModelUrlNormalizer.normalize("https://api.example.com/v1/")
        );
    }

    @Test
    void shouldCollapseDuplicateSlashesInPath() {
        assertEquals(
                "https://api.example.com/openai/v1",
                RuntimeModelUrlNormalizer.normalize("https://api.example.com//openai///v1/")
        );
    }

    @Test
    void shouldAcceptHttpAndHttpsUrls() {
        assertTrue(RuntimeModelUrlNormalizer.isSupportedHttpUrl("https://api.example.com/v1"));
        assertTrue(RuntimeModelUrlNormalizer.isSupportedHttpUrl("http://localhost:11434/v1"));
    }

    @Test
    void shouldRejectMissingScheme() {
        assertFalse(RuntimeModelUrlNormalizer.isSupportedHttpUrl("api.example.com/v1"));
    }
}
