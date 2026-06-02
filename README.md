# AI Service Deployment

Projet IA / MLOps autour du modele `google/flan-t5-base`, expose via une API `FastAPI`, conteneurise avec `Docker`, deployee sur `Google Cloud Platform`, automatise avec `GitHub Actions`, et teste via une interface web.

## Objectif

Ce projet montre comment :
- integrer un modele Hugging Face dans une API web
- deployer l'application sur des VM GCP
- automatiser le build et le deploiement avec une pipeline CI/CD
- separer les environnements `test` et `production`
- mettre en place un `load balancer`, un `Managed Instance Group` et l'`autoscaling`
- proposer une interface web simple pour tester le modele en conditions reelles

## Stack technique

- `Python`
- `FastAPI`
- `Transformers`
- `PyTorch CPU`
- `Docker`
- `Docker Compose`
- `GitHub Actions`
- `Google Cloud Compute Engine`
- `Artifact Registry`
- `Managed Instance Group`
- `Load Balancer`

## Fonctionnalites

- API FastAPI pour interroger le modele `FLAN-T5`
- endpoint de sante `/health`
- endpoint de generation `/generate`
- interface web accessible via `/app`
- deploiement local avec `docker compose`
- deploiement `test` et `prod` sur GCP
- pipeline CI/CD avec promotion `test -> prod`
- image Docker publiee dans `Artifact Registry`
- support du load balancing et de l'autoscaling

## Structure du projet

- `main.py` : API FastAPI et logique de generation
- `Dockerfile` : image applicative
- `docker-compose.yml` : execution locale
- `docker-compose.prod.yml` : execution deployee
- `startup-mig.sh` : script de demarrage des VM du MIG
- `.github/workflows/deploy.yml` : build et deploiement `test`
- `.github/workflows/deploy-prod.yml` : promotion/deploiement `prod`
- `DEPLOYMENT_PLAN.md` : plan d'evolution et notes d'infra
- `static/index.html` : interface web
- `static/app.js` : logique front
- `static/styles.css` : style de l'interface

## Endpoints

- `GET /`
  - verifie que l'API est disponible
- `GET /health`
  - verifie que le modele est charge
- `GET /generate?prompt=...`
  - genere une reponse a partir d'un prompt
- `POST /generate`
  - accepte un JSON avec `prompt`, `mode` et `tone`
- `GET /app`
  - ouvre l'interface web

## Lancer le projet en local

### Installation Python

```powershell
pip install -r requirements.txt
```

### Demarrage en local

```powershell
uvicorn main:app --reload
```

Puis ouvrez :

- API : `http://localhost:8000`
- Sante : `http://localhost:8000/health`
- App web : `http://localhost:8000/app`

## Lancer avec Docker Compose

```powershell
docker compose up -d --build
```

Puis ouvrez :

- `http://localhost:8000/health`
- `http://localhost:8000/app`

## Deploiement GCP

Le projet a ete deployee sur `Google Cloud Platform` avec :

- une VM `test`
- une VM `prod`
- un `Artifact Registry`
- des secrets GitHub
- une CI/CD `GitHub Actions`

### Flux de deploiement

1. push sur `main`
2. build de l'image Docker
3. push dans `Artifact Registry`
4. deploiement sur `test`
5. verification `/health`
6. promotion automatique vers `prod`
7. verification `/health` en production

## CI/CD

### Workflow test

Le workflow `deploy.yml` :

- build l'image Docker
- pousse l'image avec un tag `SHA`
- pousse aussi le tag `latest`
- deploie sur la VM `test`
- verifie la sante du service

### Workflow prod

Le workflow `deploy-prod.yml` :

- se declenche apres succes du workflow `test`
- deploie sur la VM `prod`
- verifie la sante du service

## Load balancing et autoscaling

Le projet inclut une architecture scalable sur GCP avec :

- un `Instance Template`
- un `Managed Instance Group`
- un `Health Check` sur `/health`
- un `HTTP Load Balancer`
- l'`autoscaling`

Le script `startup-mig.sh` sert a :

- installer Docker
- s'authentifier a `Artifact Registry`
- lancer l'application dans les VM creees par le MIG

## Interface web

L'interface web permet :

- de saisir un prompt
- de choisir un scenario
- de choisir un style de reponse
- de tester visuellement le comportement du modele

Acces :

- local : `http://localhost:8000/app`
- derriere le load balancer : `http://LOAD_BALANCER_IP/app`

## Limites actuelles

- `flan-t5-base` reste un modele de taille moderee
- la qualite des reponses peut varier selon les prompts
- certains cas d'usage tres libres necessitent un modele plus puissant pour un rendu plus stable

## Evolutions possibles

- tester un modele plus performant
- ajouter HTTPS au load balancer
- renforcer le monitoring
- historiser les requetes
- ajouter l'authentification utilisateur
- enrichir l'interface web

## Exemple de tests

### Sante

```powershell
curl http://localhost:8000/health
```

### Generation

```powershell
curl "http://localhost:8000/generate?prompt=Explain%20AI%20simply"
```

### App web

Ouvrir :

```text
http://localhost:8000/app
```

## Auteur

Projet realise dans une logique de deploiement IA / MLOps autour de `FastAPI`, `Docker`, `GitHub Actions` et `Google Cloud`.
