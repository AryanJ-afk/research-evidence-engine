const form = document.querySelector("#question-form");
const questionInput = document.querySelector("#question");
const submitButton = document.querySelector("#submit-button");
const exampleButtons = document.querySelectorAll(".example");

const requestStatus = document.querySelector("#request-status");
const errorMessage = document.querySelector("#error-message");
const results = document.querySelector("#results");
const resultMeta = document.querySelector("#result-meta");
const answeredQuestion = document.querySelector("#answered-question");
const answerContent = document.querySelector("#answer-content");
const sourcesPanel = document.querySelector("#sources-panel");
const sourceList = document.querySelector("#source-list");
const resultsGrid = document.querySelector(".results-grid");

function setBusy(busy) {
    submitButton.disabled = busy;
    questionInput.readOnly = busy;
    form.setAttribute("aria-busy", String(busy));

    submitButton.textContent = busy
        ? "Finding evidence..."
        : "Find evidence →";

    exampleButtons.forEach((button) => {
        button.disabled = busy;
    });
}

function renderResponse(data) {
    answerContent.replaceChildren();
    sourceList.replaceChildren();

    answeredQuestion.textContent = data.question;

    const sources = data.sources;
    const sourceElements = new Map();

    sources.forEach((source, index) => {
        const card = document.createElement("details");
        card.className = "source-card";
        card.id = `source-${index + 1}`;

        const heading = document.createElement("summary");
        heading.textContent = `[${index + 1}] ${source.title}`;

        const abstract = document.createElement("p");
        abstract.textContent = source.abstract;

        const link = document.createElement("a");
        link.href = `https://arxiv.org/abs/${source.arxiv_id}`;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = `Read on arXiv · ${source.arxiv_id} ↗`;

        card.append(heading, abstract, link);
        sourceList.append(card);

        sourceElements.set(source.arxiv_id, {
            number: index + 1,
            element: card,
        });
    });

    if (data.status === "insufficient_evidence") {
        const message = document.createElement("p");
        message.className = "claim";
        message.textContent = data.answer;
        answerContent.append(message);
    } else {
        data.claims.forEach((claim) => {
            const paragraph = document.createElement("p");
            paragraph.className = "claim";
            paragraph.textContent = claim.text;

            claim.paper_ids.forEach((paperId) => {
                const source = sourceElements.get(paperId);

                if (!source) return;

                const citation = document.createElement("a");
                citation.className = "citation";
                citation.href = `#${source.element.id}`;
                citation.textContent = `[${source.number}]`;
                citation.setAttribute(
                    "aria-label",
                    `Open source ${source.number}`,
                );

                citation.addEventListener("click", () => {
                    source.element.open = true;
                });

                paragraph.append(citation);
            });

            answerContent.append(paragraph);
        });
    }

    const hasSources = sources.length > 0;
    sourcesPanel.hidden = !hasSources;
    resultsGrid.classList.toggle("no-sources", !hasSources);

    const seconds = (data.pipeline_ms / 1000).toFixed(1);

    resultMeta.textContent = data.status === "answered"
        ? `${sources.length} cited sources · ${seconds}s`
        : `Insufficient evidence · ${seconds}s`;

    results.hidden = false;
}

exampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
        questionInput.value = button.textContent.trim();
        questionInput.focus();
    });
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        questionInput.focus();
        return;
    }

    errorMessage.hidden = true;
    results.hidden = true;
    requestStatus.textContent =
        "Retrieving research abstracts and preparing an answer…";

    setBusy(true);

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();

        if (!response.ok) {
            const message = typeof data.detail === "string"
                ? data.detail
                : "The request could not be completed. Please try again.";

            throw new Error(message);
        }

        if (
            !["answered", "insufficient_evidence"].includes(data.status) ||
            !Array.isArray(data.claims) ||
            !Array.isArray(data.sources)
        ) {
            throw new Error("The server returned an unexpected response.");
        }

        renderResponse(data);

        requestStatus.textContent = data.status === "answered"
            ? "Answer ready. Select a citation to inspect its evidence."
            : "The retrieved evidence was insufficient for this question.";
    } catch (error) {
        requestStatus.textContent = "";
        errorMessage.textContent = error.message;
        errorMessage.hidden = false;
    } finally {
        setBusy(false);
    }
});