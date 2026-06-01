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

## 8. Load balancing et autoscaling sur GCP

### Architecture cible

- Une image Docker stable dans Artifact Registry.
- Un `instance template` avec `startup script`.
- Un `Managed Instance Group` (MIG) base sur ce template.
- Un `health check` HTTP sur `/health`.
- Un `backend service`.
- Un `HTTP load balancer`.
- Un `autoscaler`.

### Startup script recommande

Le fichier [startup-mig.sh](C:/Users/Snell%20Nonkala/Documents/py/startup-mig.sh) est prevu pour les futures VM du MIG.

Ce script :
- installe Docker et Docker Compose
- installe `gcloud`
- configure Docker pour Artifact Registry
- cree un `docker-compose.yml`
- pull l'image Docker
- lance l'API
- attend que `http://localhost:8000/health` reponde

### Procedure detaillee en console GCP

#### Etape 1. Verifier les prerequis

- Votre image Docker doit deja etre dans Artifact Registry.
- Le service account du futur template doit avoir `Artifact Registry Reader`.
- Le port 8000 doit etre autorise entre le load balancer et les VM.
- L'endpoint `/health` doit repondre correctement.

#### Etape 2. Creer un instance template

Chemin :
- `Compute Engine`
- `Instance templates`
- `Create instance template`

Champs recommandes :
- Name : `flan-api-template-v1`
- Region : `europe-west9`
- Machine type : commencez simple, par exemple `e2-medium` ou `e2-standard-2`
- Boot disk : Ubuntu LTS
- Service account : un compte ayant `Artifact Registry Reader`
- Access scopes : `Allow full access to all Cloud APIs`

Dans `Advanced options` :
- `Management`
- `Automation`
- `Startup script`

Collez le contenu du fichier `startup-mig.sh`.

#### Etape 3. Ajouter un tag reseau

Dans le template, ajoutez un tag reseau par exemple :
- `flan-api`

Ce tag servira a appliquer la regle firewall du port 8000.

#### Etape 4. Creer la regle firewall

Chemin :
- `VPC network`
- `Firewall`
- `Create firewall rule`

Valeurs recommandees :
- Name : `allow-flan-api-8000`
- Targets : `Specified target tags`
- Target tags : `flan-api`
- Source filter : `IPv4 ranges`
- Source IPv4 ranges : utilisez au minimum votre plage de test ou plus tard les plages du load balancer
- Protocols and ports : `tcp:8000`

#### Etape 5. Creer le Managed Instance Group

Chemin :
- `Compute Engine`
- `Instance groups`
- `Create instance group`

Valeurs recommandees :
- Name : `flan-api-mig`
- Instance template : `flan-api-template-v1`
- Location type : commencez par `Single zone`
- Zone : `europe-west9-b`
- Number of instances : `2`

Pourquoi `2` :
- une base simple pour tester le load balancing
- meilleure disponibilite qu'une seule VM

#### Etape 6. Creer le health check

Chemin :
- `Network services`
- `Load balancing`
- `Health checks`
- `Create health check`

Valeurs recommandees :
- Name : `flan-api-health-check`
- Protocol : `HTTP`
- Port : `8000`
- Request path : `/health`
- Check interval : `10s`
- Timeout : `5s`

#### Etape 7. Creer le backend service

Chemin :
- `Network services`
- `Load balancing`
- `Create load balancer`

Choisissez :
- `Application Load Balancer`
- `From internet to my VMs`
- `Global external Application Load Balancer`

Dans la partie backend :
- creez un backend service
- ajoutez le `Managed Instance Group`
- attachez le `health check` `flan-api-health-check`

#### Etape 8. Creer le frontend

Dans le load balancer :
- choisissez HTTP pour commencer
- reservez une IP externe si vous voulez une adresse stable
- gardez le port 80 pour un premier test

Plus tard, vous pourrez ajouter HTTPS.

#### Etape 9. Activer l'autoscaling

Chemin :
- `Compute Engine`
- `Instance groups`
- cliquez sur `flan-api-mig`
- `Edit`
- section `Autoscaling`

Valeurs de depart conseillees :
- Minimum number of instances : `2`
- Maximum number of instances : `5`
- Autoscaling signal : `CPU utilization`
- Target CPU utilization : `60%`

#### Etape 10. Tester

- Recuperez l'IP du load balancer.
- Testez :
  - `curl http://LOAD_BALANCER_IP/health`
- Puis testez :
  - `curl "http://LOAD_BALANCER_IP/generate?prompt=Explain%20AI%20simply"`

Pour un test de charge :
- utilisez `hey`, `k6` ou `locust`
- observez si le MIG cree de nouvelles VM

### Points d'attention

- Un MIG demande des VM identiques et interchangeables.
- Ne partez pas de vos VM configurees a la main comme base du load balancer.
- Le startup script doit suffire a reconstruire une VM saine.
- Pour une architecture plus robuste, passez ensuite a un `regional MIG`.
