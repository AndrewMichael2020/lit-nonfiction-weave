document.addEventListener("DOMContentLoaded", () => {
    const generateBtn = document.getElementById("generate-btn");
    const premiseInput = document.getElementById("premise");
    const venueInput = document.getElementById("venue");
    const storyOutput = document.getElementById("story-output");
    const metricsOutput = document.getElementById("metrics-output");
    const claimsOutput = document.getElementById("claims-output");

    generateBtn.addEventListener("click", () => {
        const premise = premiseInput.value;
        const venue = venueInput.value;

        // Dummy data for demonstration
        const dummyStory = {
            story: `This is a generated story based on the premise: "${premise}" for the venue: "${venue}". It is a story about youth, mountains, and the stillness that follows ascent. The narrative explores the complexities of memory and loss, set against the backdrop of a vast, unforgiving landscape. The protagonist, a young climber, grapples with a past trauma that resurfaces during a challenging expedition. The story is written in a literary style, suitable for a publication like The New Yorker.`,
            metrics: {
                word_count: 4500,
                within_band: true,
                grit_score: 0.85,
                specificity: 0.72,
                passive_ratio: 0.15
            },
            claims: [
                { claim: "The protagonist is a young climber.", source: "Character description" },
                { claim: "The story is set in the mountains.", source: "Setting details" },
                { claim: "The protagonist is dealing with past trauma.", source: "Plot point" }
            ]
        };

        storyOutput.textContent = dummyStory.story;
        metricsOutput.textContent = JSON.stringify(dummyStory.metrics, null, 2);
        claimsOutput.textContent = JSON.stringify(dummyStory.claims, null, 2);
    });
});
