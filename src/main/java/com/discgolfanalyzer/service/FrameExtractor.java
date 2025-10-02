package com.discgolfanalyzer.service;

import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.*;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class FrameExtractor {

    public static class Frames {
        public List<Path> paths;
        public int widthPx;
        public double fpsUsed;
    }

    /**
     * Extract frames using ffmpeg.
     * Example command created:
     *   ffmpeg -y -i input.mp4 -t {maxSeconds} -vf fps={fps},scale=720:-1 -q:v 3 outdir/frame_%04d.jpg
     */
    public Frames extractFrames(Path videoFile, Path outDir, double fps, int maxSeconds)
            throws IOException, InterruptedException {

        Files.createDirectories(outDir);

        Process proc = new ProcessBuilder(
                "ffmpeg",
                "-y",
                "-i", videoFile.toString(),
                "-t", String.valueOf(maxSeconds),
                "-vf", String.format("fps=%s,scale=720:-1", fps),
                "-q:v", "3",
                outDir.resolve("frame_%04d.jpg").toString()
        ).redirectErrorStream(true).start();

        try (BufferedReader br = new BufferedReader(new InputStreamReader(proc.getInputStream()))) {
            while (br.readLine() != null) { /* drain output */ }
        }
        int code = proc.waitFor();
        if (code != 0) throw new IOException("ffmpeg failed with exit code " + code);

        List<Path> frames = Files.list(outDir)
                .filter(p -> p.getFileName().toString().toLowerCase().endsWith(".jpg"))
                .sorted()
                .collect(Collectors.toList());

        int width = 0;
        if (!frames.isEmpty()) {
            BufferedImage img = ImageIO.read(frames.get(0).toFile());
            width = img.getWidth();
        }

        Frames f = new Frames();
        f.paths = frames;
        f.widthPx = width;
        f.fpsUsed = fps;
        return f;
    }
}
