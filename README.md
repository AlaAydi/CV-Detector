# 🎯 AI Resume Optimizer

> Analysez la compatibilité entre un CV et une offre d'emploi, obtenez un score ATS détaillé, identifiez les compétences manquantes et générez un CV optimisé — **sans jamais inventer d'informations**.

[![Angular](https://img.shields.io/badge/Angular-19-DD0031?logo=angular&logoColor=white)](https://angular.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-local-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/license-private-lightgrey)]()

---

## 📖 Sommaire

- [Aperçu](#-aperçu)
- [Stack technique](#-stack-technique)
- [Prérequis](#-prérequis)
- [Démarrage rapide](#-démarrage-rapide)
  - [1. Base de données PostgreSQL](#1-base-de-données-postgresql)
  - [2. Backend (FastAPI)](#2-backend-fastapi)
  - [3. Frontend (Angular)](#3-frontend-angular)
- [Fonctionnalités MVP](#-fonctionnalités-mvp)
- [Endpoints principaux](#-endpoints-principaux)
- [Formule du score ATS](#-formule-du-score-ats)
- [Structure du projet](#-structure-du-projet)
- [Support](#-support)

---

## 🧭 Aperçu

**AI Resume Optimizer** aide les candidats à adapter leur CV à une offre d'emploi précise. L'application compare le contenu du CV à la description du poste, calcule un score de compatibilité ATS *(Applicant Tracking System)*, met en évidence les compétences manquantes et propose un CV réorganisé — en s'appuyant uniquement sur les informations réellement présentes dans le document original.

**Principes clés :**

| Garantie | Description |
|---|---|
| ✅ Zéro invention | Aucune compétence ou expérience n'est ajoutée si elle ne figure pas déjà dans le CV. |
| ⚡ Résultat rapide | Score ATS calculé en quelques secondes. |
| 📄 Formats supportés | Import et export en PDF et DOCX. |

---

## 🛠 Stack technique

| Couche | Technologie |
|---|---|
| **Frontend** | Angular 19 + Angular Material |
| **Backend** | FastAPI + SQLAlchemy |
| **Base de données** | PostgreSQL (instance locale) |
| **NLP / Matching** | scikit-learn + dictionnaire de synonymes |

---

## ✅ Prérequis

Avant de démarrer, assure-toi d'avoir installé :

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) et npm
- [PostgreSQL 14+](https://www.postgresql.org/download/) (installé et lancé localement)

---

## 🚀 Démarrage rapide

### 1. Base de données PostgreSQL

Aucun conteneur Docker n'est nécessaire : le backend se connecte à une instance PostgreSQL locale.

Configuration attendue par défaut (`backend/.env`) :

| Paramètre | Valeur par défaut |
|---|---|
| Hôte | `localhost` |
| Port | `5432` |
| Base | `iacv` |
| Utilisateur | `iacv` |
| Mot de passe | `iacv` |

Si PostgreSQL n'est pas encore installé, installe-le puis crée la base et l'utilisateur correspondants — ou ajuste `backend/.env` pour pointer vers ta propre instance.

```sql
CREATE DATABASE iacv;
CREATE USER iacv WITH PASSWORD 'iacv';
GRANT ALL PRIVILEGES ON DATABASE iacv TO iacv;
```

### 2. Backend (FastAPI)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

| Ressource | URL |
|---|---|
| API | http://localhost:8000 |
| Documentation Swagger | http://localhost:8000/docs |

### 3. Frontend (Angular)

```bash
cd frontend
npm install
npm start
```

| Ressource | URL |
|---|---|
| Application | http://localhost:4200 |

---

## ✨ Fonctionnalités MVP

- 📤 Upload de CV (PDF / DOCX)
- 🔍 Analyse du CV par rapport à une description de poste
- 📊 Score ATS global + détail par critère (compétences, mots-clés, expérience, formation)
- 🧩 Détection des compétences présentes / manquantes
- 💡 Recommandations d'amélioration personnalisées
- 📝 Génération d'un CV optimisé (réorganisation du contenu, sans invention)
- 📥 Export du CV optimisé en PDF / DOCX
- 🔐 Authentification JWT, historique des analyses et tableau de bord

---

## 🔌 Endpoints principaux

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Inscription d'un nouvel utilisateur |
| `POST` | `/api/auth/login` | Connexion et récupération du token JWT |
| `POST` | `/api/resumes/upload` | Upload d'un CV |
| `POST` | `/api/analysis/match` | Analyse du CV par rapport à une offre |
| `GET` | `/api/analysis/history` | Historique des analyses *(authentifié)* |
| `GET` | `/api/analysis/{id}/download/{format}` | Export du CV optimisé (`format` = `pdf` ou `docx`) |

> 📚 La documentation interactive complète de l'API est disponible sur [`/docs`](http://localhost:8000/docs) une fois le backend lancé.

---

## 🧮 Formule du score ATS

Le score global est une moyenne pondérée de quatre critères :

```
Score ATS = 40% Compétences + 30% Mots-clés + 20% Expérience + 10% Formation
```

| Critère | Poids | Description |
|---|---|---|
| Compétences | 40 % | Correspondance entre les compétences du CV et celles requises par l'offre |
| Mots-clés | 30 % | Présence des termes clés de l'offre dans le CV |
| Expérience | 20 % | Pertinence et durée des expériences par rapport au poste |
| Formation | 10 % | Adéquation du parcours académique avec les prérequis |

---

## 🗂 Structure du projet

```
iacv/
├── backend/          # API FastAPI (SQLAlchemy, NLP, auth JWT)
└── frontend/          # Application Angular (UI, dashboard, analyse)
```

---

## 💬 Support

Pour toute question, bug ou suggestion, ouvre une *issue* sur le dépôt du projet.
