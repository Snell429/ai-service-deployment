# Plan d'evolution du projet

## 1. Se connecter proprement a la VM GCP

- Installer un client SSH.
  - Windows: utiliser `OpenSSH` inclus dans PowerShell ou `PuTTY`.
  - macOS / Linux: `ssh` est deja disponible.
- Generer une paire de cles:
  - `ssh-keygen -t ed25519 -C "gcp-vm"`
- Ajouter la cle publique sur la VM GCP.
  - Soit dans les metadonnees du projet ou de l'instance.
  - Soit avec `gcloud compute ssh`.
- Tester la connexion:
  - `ssh USER@VM_IP`

## 2. Rediger des specifications detaillees avant de coder

Utiliser un prompt structure pour Codex:

```text
Je veux faire evoluer mon application FastAPI deployee sur GCP.

Contexte actuel:
- API FastAPI pour inference NLP avec le modele Hugging Face google/flan-t5-base
- Application dockerisee et deja deployee sur une VM GCP
- Endpoint principal: /generate?prompt=...

Objectifs:
- industrialiser le deploiement
- utiliser docker-compose
- mettre en place CI/CD GitHub Actions
- preparer le support GPU
- preparer load balancing et autoscaling

Contraintes:
- garder FastAPI
- deploiement sur GCP
- privilegier une architecture simple et evolutive

Livrables attendus:
- architecture cible
- fichiers a creer/modifier
- workflow CI/CD
- strategie de secrets
- procedure de deploiement
- plan de tests

Donne-moi directement les fichiers a creer et leur contenu.
```

## 3. Passer de docker run a docker-compose

- Centraliser la configuration dans `docker-compose.yml`.
- Declarer les variables d'environnement du modele.
- Utiliser `restart: unless-stopped`.
- Standardiser la commande:
  - `docker compose up -d --build`

## 4. Connecter GitHub a la CI/CD

- Le depot GitHub existe deja.
- Creer un service account GCP avec acces a Artifact Registry.
- Ajouter dans GitHub Secrets:
  - `GCP_PROJECT_ID`
  - `GCP_REGION`
  - `GCP_ARTIFACT_REPO`
  - `GCP_SA_KEY`
  - `VM_HOST`
  - `VM_USER`
  - `VM_SSH_KEY`
- Pipeline recommande:
  - build image Docker
  - push vers Artifact Registry
  - connexion SSH a la VM
  - `docker compose -f docker-compose.prod.yml pull`
  - `docker compose -f docker-compose.prod.yml up -d`

## 5. Tester l'ajout de GPU sur GCP

- Verifier si votre type de VM accepte un GPU.
- Sur GCP, tester par exemple une VM compatible `n1-standard` ou `g2`.
- Installer les drivers NVIDIA sur la VM.
- Installer `nvidia-container-toolkit`.
- Tester:
  - `nvidia-smi`
  - `docker run --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi`
- Si cela fonctionne, adapter ensuite l'image Docker pour PyTorch avec support CUDA.

## 6. Tester load balancing et autoscaling

- Pour plusieurs VMs, viser plutot:
  - Managed Instance Group
  - Instance Template
  - HTTP Load Balancer GCP
- Point d'attention:
  - les modeles NLP sont lourds au demarrage
  - l'autoscaling doit tenir compte du temps de warm-up
- Faire des tests de charge avec:
  - `hey`
  - `k6`
  - `locust`

## 7. Ordre recommande

1. Corriger et stabiliser l'image Docker.
2. Passer a `docker-compose`.
3. Mettre en place GitHub Actions + Artifact Registry.
4. Automatiser le deploiement sur la VM.
5. Tester ensuite GPU sur une VM dediee.
6. Enfin, tester load balancing et autoscaling.
