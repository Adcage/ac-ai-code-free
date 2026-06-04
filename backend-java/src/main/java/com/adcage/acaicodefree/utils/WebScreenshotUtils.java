package com.adcage.acaicodefree.utils;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import com.adcage.acaicodefree.model.enums.BrowserTypeEnum;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.FileImageOutputStream;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.time.Duration;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Iterator;

public final class WebScreenshotUtils {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy/MM/dd");

    private WebScreenshotUtils() {
    }

    /**
     * 使用默认浏览器（Chrome）截图
     */
    public static File captureAndCompress(String url, String tempDir, Integer width, Integer height,
                                          Long waitAfterLoadMillis, Float compressionQuality) throws IOException {
        return captureAndCompress(url, tempDir, width, height, waitAfterLoadMillis, compressionQuality, BrowserTypeEnum.CHROME);
    }

    /**
     * 根据指定浏览器类型截图
     */
    public static File captureAndCompress(String url, String tempDir, Integer width, Integer height,
                                          Long waitAfterLoadMillis, Float compressionQuality,
                                          BrowserTypeEnum browserType) throws IOException {
        File targetDir = new File(tempDir, DATE_FORMATTER.format(LocalDate.now()));
        FileUtil.mkdir(targetDir);
        String fileId = IdUtil.simpleUUID();
        File rawFile = new File(targetDir, fileId + ".png");
        File compressedFile = new File(targetDir, fileId + "_compressed.jpg");
        WebDriver webDriver = null;
        try {
            webDriver = WebDriverFactory.createDriver(browserType, width, height);
            webDriver.get(url);
            waitForPageFullyRendered(webDriver, waitAfterLoadMillis);
            File screenshot = ((TakesScreenshot) webDriver).getScreenshotAs(OutputType.FILE);
            FileUtil.copy(screenshot, rawFile, true);
            compressToJpg(rawFile, compressedFile, compressionQuality);
            return compressedFile;
        } finally {
            if (webDriver != null) {
                webDriver.quit();
            }
            deleteIfExists(rawFile);
        }
    }

    public static void deleteIfExists(File file) {
        if (file == null) {
            return;
        }
        if (file.exists()) {
            FileUtil.del(file);
        }
    }

    private static void waitForPageFullyRendered(WebDriver webDriver, Long waitAfterLoadMillis) {
        new WebDriverWait(webDriver, Duration.ofSeconds(15)).until(driver -> {
            Object readyState = ((JavascriptExecutor) driver).executeScript("return document.readyState");
            return "complete".equals(readyState);
        });
        if (waitAfterLoadMillis != null && waitAfterLoadMillis > 0) {
            try {
                Thread.sleep(waitAfterLoadMillis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private static void compressToJpg(File source, File target, Float compressionQuality) throws IOException {
        BufferedImage bufferedImage = ImageIO.read(source);
        if (bufferedImage == null) {
            throw new IOException("读取截图文件失败");
        }
        Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName("jpg");
        if (!writers.hasNext()) {
            throw new IOException("未找到 JPG 图片写入器");
        }
        ImageWriter imageWriter = writers.next();
        ImageWriteParam imageWriteParam = imageWriter.getDefaultWriteParam();
        if (imageWriteParam.canWriteCompressed()) {
            imageWriteParam.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
            float quality = compressionQuality == null ? 0.3f : compressionQuality;
            imageWriteParam.setCompressionQuality(Math.max(0.05f, Math.min(1.0f, quality)));
        }
        try (FileImageOutputStream outputStream = new FileImageOutputStream(target)) {
            imageWriter.setOutput(outputStream);
            imageWriter.write(null, new IIOImage(bufferedImage, null, null), imageWriteParam);
        } finally {
            imageWriter.dispose();
        }
    }
}
