const healthBadge = document.getElementById("health-badge");
const modelName = document.getElementById("model-name");
const promptInput = document.getElementById("prompt");
const presetSelect = document.getElementById("preset");
const toneSelect = document.getElementById("tone");
const resultBox = document.getElementById("result");
const requestState = document.getElementById("request-state");
const generateButton = document.getElementById("generate-btn");
const clearButton = document.getElementById("clear-btn");

const presetPrompts = {
  summary: "Redige directement en francais un resume professionnel en 5 lignes expliquant l'interet de deployer une API NLP dans une entreprise.",
  email: "Redige un email professionnel annonçant qu'une API NLP a ete deployee avec succes sur Google Cloud et qu'elle est prete pour les tests utilisateurs.",
  comparison: "Compare en quelques phrases les avantages d'une architecture avec une seule VM par rapport a une architecture avec load balancer et autoscaling.",
  explanation: "Explique simplement a un responsable non technique ce que signifient load balancing et autoscaling pour une API web.",
};

promptInput.value = presetPrompts.explanation;

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
    resultBox.textContent = "Veuillez saisir un prompt.";
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
  }
});

checkHealth();
