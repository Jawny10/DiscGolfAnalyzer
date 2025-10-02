package com.discgolfanalyzer.service;

import com.openai.OpenAI;
import com.openai.api.models.ChatCompletionCreateRequest;
import com.openai.api.models.ChatCompletionMessage;
import com.openai.api.models.ChatCompletionResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class OpenAiVisionService {

    private final OpenAI client;

    public OpenAiVisionService(@Value("${openai.api.key}") String apiKey) {
        this.client = OpenAI.builder()
                .apiKey(apiKey)
                .build();
    }

    /**
     * Analyze a disc golf throw image or video frame using GPT-4o-mini (vision-capable).
     *
     * @param base64Image Base64-encoded frame or still from the video
     * @return String analysis from GPT
     */
    public String analyzeThrowFromImage(String base64Image) {
        ChatCompletionCreateRequest request = ChatCompletionCreateRequest.builder()
                .model("gpt-4o-mini") // vision + text model
                .messages(List.of(
                        ChatCompletionMessage.systemMessage("You are a professional disc golf coach. Analyze the player's throwing form."),
                        ChatCompletionMessage.userMessageWithImage(
                                "Analyze this throw and provide technique feedback plus estimate release speed.",
                                base64Image
                        )
                ))
                .maxTokens(500)
                .build();

        ChatCompletionResult result = client.chat().create(request);
        return result.getChoices().get(0).getMessage().getContent().get(0).getText();
    }
}
