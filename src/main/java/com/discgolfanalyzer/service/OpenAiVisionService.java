package com.discgolfanalyzer.service;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.models.ChatModel;
import com.openai.models.chat.completions.ChatCompletion;
import com.openai.models.chat.completions.ChatCompletionCreateParams;

import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;


@Service
@ConditionalOnProperty(name = "openai.java.enabled", havingValue = "true", matchIfMissing = false)
public class OpenAiVisionService {

    private final OpenAIClient client;

    public OpenAiVisionService() {
        // Reads OPENAI_API_KEY (and optional OPENAI_ORG_ID/OPENAI_PROJECT_ID) from env
        this.client = OpenAIOkHttpClient.fromEnv();
    }

    /** Simple helper used elsewhere (kept if you already call it). */
    public String analyzeThrow(String imageUrl, String userPrompt) {
        String combinedPrompt = """
            You are a disc golf throwing technique analyst.
            Media (may be an image or video URL): %s
            Task: %s

            If it's a video, describe key form checkpoints (reachback, plant, hip/shoulder separation,
            nose angle, follow-through) and give concise, numbered tips.
            """.formatted(imageUrl == null ? "(none provided)" : imageUrl,
                          userPrompt == null ? "Analyze the throw." : userPrompt);

        ChatCompletionCreateParams params = ChatCompletionCreateParams.builder()
            .addUserMessage(combinedPrompt)
            .model(ChatModel.GPT_4O_MINI) // vision/multimodal capable; efficient
            .build();

        ChatCompletion completion = client.chat().completions().create(params);

        // content() is Optional<String>, not a list—use orElse(...)
        if (completion.choices().isEmpty()) return "(No analysis returned)";
        return completion.choices().get(0).message().content().orElse("(No content)");
    }

    /**
     * ADD THIS: matches the controller's expected signature.
     * The controller calls visionService.analyzeFrames(frames, fps, totalFrames, height, distance).
     * We summarize a few filenames and pass a structured prompt to OpenAI.
     */
    public String analyzeFrames(
            List<Path> framePaths,
            double fps,
            int totalFrames,
            Double playerHeightMeters,
            Double cameraDistanceMeters
    ) {
        String sampleNames = (framePaths == null || framePaths.isEmpty())
                ? "(no frames)"
                : framePaths.stream()
                    .limit(5)
                    .map(p -> p == null ? "null" : String.valueOf(p.getFileName()))
                    .collect(Collectors.joining(", "));

        String prompt = """
            You are a disc golf throw analyst.
            We extracted %d frames at %.2f fps. Example frame files: %s
            Player height (m): %s
            Camera distance (m): %s

            1) Identify reachback position, plant timing, hip/shoulder separation, nose angle, and follow-through cues.
            2) Give 3–5 concise, numbered tips to improve form.
            3) If info is insufficient, state assumptions clearly.
            """
            .formatted(
                totalFrames,
                fps,
                sampleNames,
                playerHeightMeters == null ? "unknown" : playerHeightMeters.toString(),
                cameraDistanceMeters == null ? "unknown" : cameraDistanceMeters.toString()
            );

        ChatCompletionCreateParams params = ChatCompletionCreateParams.builder()
            .addUserMessage(prompt)
            .model(ChatModel.GPT_4O_MINI)
            .build();

        ChatCompletion completion = client.chat().completions().create(params);

        if (completion.choices().isEmpty()) return "(No analysis returned)";
        return completion.choices().get(0).message().content().orElse("(No content)");
    }
}
