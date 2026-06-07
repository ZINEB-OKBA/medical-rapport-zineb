# 🏥 OrientaClin — Système Multi-Agents d'Orientation Clinique Préliminaire

OrientaClin est un projet d'ingénierie logicielle appliquée à la santé, spécialisé en **Intelligence Artificielle et Big Data**. Il implémente une architecture multi-agents dynamique pour l'orientation clinique préliminaire en utilisant **LangGraph**, **FastAPI** et **Streamlit**, le tout propulsé par le LLM **Llama-3.3-70B via Groq**.

## 🚀 Fonctionnalités Clés
- **Orchestration Multi-Agents :** Un agent `Supervisor` central analyse continuellement l'état partagé (`MedicalState`) pour router dynamiquement le flux vers l'agent adéquat.
- **Collecte Interactive de Données :** Un cycle itératif de 5 questions cliniques standardisées est géré de façon fluide par le `DiagnosticAgent`.
- **Human-in-the-Loop (HITL) :** Suspension native du graphe LangGraph (`interrupt_before`) pour forcer une pause de sécurité. Le médecin traitant doit valider la synthèse clinique et saisir ses directives thérapeutiques avant la génération du rapport.
- **Génération de Rapport Structuré :** Compte-rendu médical final professionnel, complet et téléchargeable au format texte.
- **Exécution Asynchrone :** Optimisation complète du graphe et des arêtes conditionnelles en `async/await` pour éliminer tout interblocage (deadlock) et garantir des réponses ultra-rapides.

---

## 📐 Architecture Technique du Système

### Flux d'Exécution du Graphe
1. **START** ➔ `Supervisor` (Évalue l'état initial)
2. `Supervisor` ➔ `DiagnosticAgent` (Boucle itérative pour les 5 questions et génération de la synthèse clinique préliminaire)
3. `Supervisor` ➔ **[PAUSE HITL]** `PhysicianReview` (Le médecin prend la main via l'API, saisit le traitement)
4. `Supervisor` ➔ `ReportAgent` (Génère le rapport final structuré)
5. `Supervisor` ➔ **END**

### Technologies Utilisées
- **LLM Core :** `ChatGroq` (Modèle `llama-3.3-70b-specdec` / `llama-3.3-70b-versatile`)
- **Orchestration :** LangGraph (`StateGraph`, `MemorySaver` pour la persistance des sessions)
- **Backend API :** FastAPI & Uvicorn (Endpoints `/consultation/start` et `/consultation/resume` pour gérer le cycle de vie de la session)
- **Frontend / UI :** Streamlit (Interface minimaliste et épurée respectant le parcours de soins utilisateur)

---

## 📋 Exemple de Rapport Généré par le Système
Voici le résultat concret d'une exécution de bout en bout (généré le 07/06/2026) :

```text
=== RAPPORT FINAL D'ORIENTATION CLINIQUE ===
Date : 07/06/2026 19:20
Référence : Évaluation clinique du patient de 38 ans

INFORMATIONS PATIENT
- Âge : 38 ans
- Symptômes principaux : Fièvre à 38,5°C depuis 2 jours, toux sèche persistante, légère fatigue
- Antécédents médicaux : Allergies à la poussière | Traitement actuel : Ferplex

SYNTHÈSE CLINIQUE PRÉLIMINAIRE
Le patient présente une fièvre à 38,5°C depuis 2 jours, accompagnée d'une toux sèche persistante et d'une légère fatigue. 
Cependant, il mentionne avoir des difficultés respiratoires depuis 2 semaines, ce qui contraste avec son état initial. 

RECOMMANDATION INTERMÉDIAIRE (LOGIQUE DE RECHERCHE DE SYMPTÔMES CRITIQUES)
⚠️ ATTENTION — Symptômes urgents détectés. Consultez un médecin ou les urgences sans délai.
⚠️ Cette recommandation ne remplace pas une consultation médicale.

DÉCISION DU MÉDECIN TRAITANT (HUMAN-IN-THE-LOOP VIA STREAMLIT)
Le médecin traitant a validé le cas et prescrit du paracétamol 1g chaque 8 heures pour gérer la fièvre et les symptômes associés.

MENTIONS LÉGALES OBLIGATOIRES
Ce rapport est issu d'un exercice académique et ne constitue pas un acte médical. Les décisions médicales doivent être prises sous la direction d'un professionnel de la santé qualifié.