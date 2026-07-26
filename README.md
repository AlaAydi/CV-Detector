# AI Resume Optimizer

Application web pour analyser la compatibilité entre un CV et une description de poste, calculer un score ATS, identifier les compétences manquantes et générer un CV optimisé **sans inventer d'informations**.

## Stack

- **Frontend** : Angular 19 + Angular Material
- **Backend** : FastAPI + SQLAlchemy
- **Base de données** : PostgreSQL local
- **NLP** : scikit-learn, dictionnaire de synonymes

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API : http://localhost:8000  
Docs : http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm start
```

App : http://localhost:4200

### Base de données locale

Le backend utilise PostgreSQL en local. Aucun service Docker n'est nécessaire.

Configuration attendue par défaut:

- hôte: `localhost`
- port: `5432`
- base: `iacv`
- utilisateur: `iacv`
- mot de passe: `iacv`

Si tu n'as pas encore PostgreSQL installé, installe-le sur ta machine puis crée la base et l'utilisateur avec ces valeurs, ou ajuste `backend/.env` pour pointer vers ton instance.

## Fonctionnalités MVP

- Upload CV (PDF / DOCX)
- Analyse vs description de poste
- Score ATS global + détail (compétences, mots-clés, expérience, formation)
- Compétences détectées / manquantes
- Recommandations d'amélioration
- CV optimisé (réorganisation sans invention)
- Export PDF / DOCX
- Auth JWT + historique + dashboard

## Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/register` | Inscription |
| POST | `/api/auth/login` | Connexion |
| POST | `/api/resumes/upload` | Upload CV |
| POST | `/api/analysis/match` | Analyse CV vs offre |
| GET | `/api/analysis/history` | Historique (auth) |
| GET | `/api/analysis/{id}/download/{pdf\|docx}` | Export CV optimisé |

## Formule ATS

```
Score = 40% compétences + 30% mots-clés + 20% expérience + 10% formation
```

## Structure

```
iacv/
├── backend/          # FastAPI
├── frontend/         # Angular
└── backend/
```
