package com.adcage.acaicodefree.utils;

import com.adcage.acaicodefree.model.enums.BrowserTypeEnum;
import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;

/**
 * WebDriver 工厂类
 * 根据浏览器类型自动创建对应的 WebDriver 实例
 * @author adcage
 */
public final class WebDriverFactory {

    private WebDriverFactory() {
    }

    /**
     * 根据浏览器类型创建 WebDriver
     *
     * @param browserType 浏览器类型枚举
     * @param width       视口宽度
     * @param height      视口高度
     * @return WebDriver 实例
     */
    public static WebDriver createDriver(BrowserTypeEnum browserType, Integer width, Integer height) {
        return switch (browserType) {
            case EDGE -> createEdgeDriver(width, height);
            case FIREFOX -> createFirefoxDriver(width, height);
            case CHROME -> createChromeDriver(width, height);
        };
    }

    /**
     * 创建 Chrome WebDriver
     */
    private static WebDriver createChromeDriver(Integer width, Integer height) {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = buildChromeOptions(width, height);
        return new ChromeDriver(options);
    }

    /**
     * 创建 Edge WebDriver
     */
    private static WebDriver createEdgeDriver(Integer width, Integer height) {
        WebDriverManager.edgedriver().setup();
        EdgeOptions options = buildEdgeOptions(width, height);
        return new EdgeDriver(options);
    }

    /**
     * 创建 Firefox WebDriver
     * 注意：Firefox 支持需要手动配置 geckodriver 到系统 PATH
     */
    private static WebDriver createFirefoxDriver(Integer width, Integer height) {
        try {
            // 尝试自动配置 Firefox 驱动
            WebDriverManager.firefoxdriver().setup();
        } catch (Exception e) {
            // 自动配置失败，尝试直接创建（假设系统已配置 PATH）
        }
        FirefoxOptions options = buildFirefoxOptions(width, height);
        return new FirefoxDriver(options);
    }

    /**
     * 构建 Chrome 浏览器选项
     */
    private static ChromeOptions buildChromeOptions(Integer width, Integer height) {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--disable-gpu");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--disable-extensions");
        options.addArguments("--disable-images");
        options.addArguments(String.format("--window-size=%d,%d", width, height));
        return options;
    }

    /**
     * 构建 Edge 浏览器选项
     */
    private static EdgeOptions buildEdgeOptions(Integer width, Integer height) {
        EdgeOptions options = new EdgeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--disable-gpu");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--disable-extensions");
        options.addArguments("--disable-images");
        options.addArguments(String.format("--window-size=%d,%d", width, height));
        return options;
    }

    /**
     * 构建 Firefox 浏览器选项
     */
    private static FirefoxOptions buildFirefoxOptions(Integer width, Integer height) {
        FirefoxOptions options = new FirefoxOptions();
        options.addArguments("--headless");
        options.addArguments("--disable-gpu");
        options.addArguments("--disable-extensions");
        options.addArguments(String.format("--width=%d", width));
        options.addArguments(String.format("--height=%d", height));
        return options;
    }
}
