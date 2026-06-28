const healthBadge = document.getElementById("health-badge");
const modelName = document.getElementById("model-name");
const promptInput = document.getElementById("prompt");
const presetSelect = document.getElementById("preset");
const toneSelect = document.getElementById("tone");
const modeHint = document.getElementById("mode-hint");
const resultBox = document.getElementById("result");
const requestState = document.getElementById("request-state");
const generateButton = document.getElementById("generate-btn");
const clearButton = document.getElementById("clear-btn");

const presetPrompts = {
  summary: `A little white cat lived in a house with his family. One day, he went outside to play in the garden and wandered too far away. Soon, he could not find his way back home.

The cat was scared and started to meow. A kind neighbor heard him and looked at his collar. She recognized the address on it.

The neighbor took the little cat back home. His family was very happy to see him again.

Since that day, the little cat always stayed close to the house.

Moral: We should be careful when we go far away from home.`,
  main_idea: `Load balancing distributes incoming requests across multiple servers. It helps an application stay available, avoid overload, and continue working even if one machine fails. This approach is common in cloud deployments.`,
  moral: `A little white cat lived in a house with his family. One day, he went outside to play in the garden and wandered too far away. Soon, he could not find his way back home.

The cat was scared and started to meow. A kind neighbor heard him and looked at his collar. She recognized the address on it.

The neighbor took the little cat back home. His family was very happy to see him again.

Since that day, the little cat always stayed close to the house.`,
  simplify: `Load balancing distributes incoming requests across multiple backend instances so that no single server becomes overwhelmed. It improves availability, scalability, and resilience in production environments.`,
  keywords: `This project deploys a Hugging Face FLAN-T5 model through a FastAPI application, containerizes it with Docker, automates CI/CD with GitHub Actions, and runs it on Google Cloud with load balancing and autoscaling.`,
};

const presetHints = {
  summary: "Le modele essaiera de produire un resume court du texte colle.",
  main_idea: "Le modele essaiera de donner l'idee centrale en une phrase.",
  moral: "Le modele essaiera d'extraire la morale ou la lecon du texte.",
  simplify: "Le modele essaiera de reformuler le texte avec des mots plus simples.",
  keywords: "Le modele essaiera d'extraire les mots-cles les plus importants.",
};

presetSelect.value = "summary";
promptInput.value = presetPrompts.summary;
modeHint.textContent = presetHints.summary;

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();

    if (!response.ok || !data.model_loaded) {
      throw new Error("Model not ready");
    }

    healthBadge.textContent = "API operationnelle";
    healthBadge.className = "badge ok";
    modelName.textContent = "Modele charge";
  } catch (error) {
    healthBadge.textContent = "API indisponible";
    healthBadge.className = "badge error";
    modelName.textContent = "Verifiez le deploiement";
  }
}

async function generateText() {
  const prompt = promptInput.value.trim();

  if (!prompt) {
    resultBox.textContent = "Veuillez saisir un texte source.";
    return;
  }

  generateButton.disabled = true;
  requestState.textContent = "Generation en cours...";
  resultBox.textContent = "Veuillez patienter...";

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        mode: presetSelect.value || "general",
        tone: toneSelect.value,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Une erreur est survenue");
    }

    resultBox.textContent = data.response || "Aucune reponse retournee.";
    requestState.textContent = "Generation terminee";
  } catch (error) {
    resultBox.textContent = `Erreur : ${error.message}`;
    requestState.textContent = "Echec";
  } finally {
    generateButton.disabled = false;
  }
}

generateButton.addEventListener("click", generateText);
clearButton.addEventListener("click", () => {
  promptInput.value = "";
  resultBox.textContent = "La reponse du modele apparaitra ici.";
  requestState.textContent = "";
});

presetSelect.addEventListener("change", () => {
  const preset = presetSelect.value;
  if (preset && presetPrompts[preset]) {
    promptInput.value = presetPrompts[preset];
    modeHint.textContent = presetHints[preset];
  }
});

checkHealth();
