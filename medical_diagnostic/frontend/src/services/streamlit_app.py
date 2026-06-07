"""
OrientaClin — Interface Streamlit
Système d'orientation clinique préliminaire multi-agents LangGraph

Lancement : streamlit run streamlit_app.py
"""
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="OrientaClin",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

API_URL = "http://127.0.0.1:8000"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;600&family=Source+Sans+3:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }

.main-header { text-align: center; padding: 1.5rem 0 0.5rem; border-bottom: 1px solid #e5e7eb; margin-bottom: 1.5rem; }
.main-header h1 { font-family: 'Lora', serif; font-size: 2rem; color: #1a4731; letter-spacing: -0.03em; margin: 0; }
.main-header p { color: #6b7280; font-size: 0.85rem; margin: 4px 0 0; font-weight: 300; }

.steps-row { display: flex; gap: 0; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; margin-bottom: 1.5rem; background: white; }
.step-cell { flex: 1; padding: 10px 6px; text-align: center; font-size: 0.72rem; color: #9ca3af; border-right: 1px solid #e5e7eb; line-height: 1.3; }
.step-cell:last-child { border-right: none; }
.step-cell.active { background: #1a4731; color: white; font-weight: 500; }
.step-cell.done { background: #ecfdf5; color: #1a4731; }
.step-num { font-size: 1.1rem; display: block; }

.info-card { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 3px solid #16a34a; border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 1rem; font-size: 0.88rem; line-height: 1.6; }
.warn-card { background: #fffbeb; border: 1px solid #fde68a; border-left: 3px solid #f59e0b; border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 1rem; font-size: 0.88rem; line-height: 1.6; }
.danger-card { background: #fef2f2; border: 1px solid #fecaca; border-left: 3px solid #ef4444; border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 1rem; font-size: 0.88rem; }
.blue-card { background: #eff6ff; border: 1px solid #bfdbfe; border-left: 3px solid #3b82f6; border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 1rem; font-size: 0.88rem; line-height: 1.6; }
.report-card { background: #fafafa; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.2rem 1.4rem; font-size: 0.87rem; line-height: 1.8; white-space: pre-wrap; font-family: 'Source Sans 3', sans-serif; }

.q-bubble { background: #ecfdf5; border-left: 3px solid #16a34a; border-radius: 6px; padding: 8px 12px; margin-bottom: 4px; font-size: 0.86rem; color: #14532d; }
.a-bubble { background: #f9fafb; border-left: 3px solid #d1d5db; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; font-size: 0.86rem; color: #374151; }

.progress-label { font-size: 0.78rem; color: #6b7280; margin-bottom: 4px; }
.disclaimer { text-align: center; font-size: 0.72rem; color: #9ca3af; border-top: 1px solid #f3f4f6; padding-top: 1rem; margin-top: 2rem; }
.thread-badge { font-size: 0.68rem; background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 12px; font-family: monospace; display: inline-block; margin-bottom: 1rem; }

.stButton > button { background-color: #1a4731 !important; color: white !important; border: none !important; border-radius: 8px !important; font-family: 'Source Sans 3', sans-serif !important; font-weight: 500 !important; padding: 0.5rem 1.4rem !important; }
.stButton > button:hover { background-color: #153d2a !important; }
.stTextArea textarea { border-radius: 8px !important; border: 1px solid #d1d5db !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 0.9rem !important; }
.stTextArea textarea:focus { border-color: #1a4731 !important; box-shadow: 0 0 0 1px #1a4731 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers API ──────────────────────────────────────────────────────────────
def api_post(path, body):
    try:
        r = requests.post(f"{API_URL}{path}", json=body, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend non accessible. Lancez : python -m uvicorn app.api:app --reload --port 8000")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        st.error(f"❌ Erreur API : {detail}")
        st.stop()


def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend non accessible.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        st.error(f"❌ Erreur API : {detail}")
        st.stop()


def check_api_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ── État Streamlit ───────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "thread_id": None,
        "patient_info": "",
        "question_count": 0,
        "patient_qa": [],
        "current_question": None,
        "diagnostic_summary": None,
        "interim_care": None,
        "physician_treatment": None,
        "final_report": None,
        "demo_text": "",          # ← variable intermédiaire pour les cas démo
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

QUESTIONS = [
    "Quels sont vos symptômes principaux et depuis combien de temps les ressentez-vous ?",
    "Avez-vous de la fièvre ? Si oui, quelle est votre température ?",
    "Avez-vous des antécédents médicaux importants (maladies chroniques, chirurgies, allergies) ?",
    "Prenez-vous des médicaments actuellement ? Si oui, lesquels ?",
    "Avez-vous d'autres symptômes associés : difficultés respiratoires, douleurs thoraciques, troubles de la conscience ?",
]

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏥 OrientaClin</h1>
    <p>Système d'orientation clinique préliminaire — Exercice académique LangGraph</p>
</div>
""", unsafe_allow_html=True)

if not check_api_health():
    st.markdown('<div class="danger-card">⚠️ <strong>Backend non accessible.</strong> Lancez d\'abord : <code>python -m uvicorn app.api:app --reload --port 8000</code></div>', unsafe_allow_html=True)
    st.stop()

# ── Steps indicator ──────────────────────────────────────────────────────────
s = st.session_state.step
steps_html = '<div class="steps-row">'
labels = ["1<br>Saisie Patient", "2<br>Questions Cliniques", "3<br>Revue Médecin", "4<br>Rapport Final"]
for i, label in enumerate(labels, 1):
    cls = "active" if i == s else ("done" if i < s else "")
    steps_html += f'<div class="step-cell {cls}"><span class="step-num">{"✓" if i < s else i}</span>{label}</div>'
steps_html += '</div>'
st.markdown(steps_html, unsafe_allow_html=True)

if st.session_state.thread_id:
    st.markdown(f'<div class="thread-badge">🔗 Session : {st.session_state.thread_id[:16]}…</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 — Saisie du cas patient
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown("### 📋 Cas Patient Initial")
    st.markdown("Décrivez le cas clinique ou les symptômes principaux du patient.")

    # Cas de démonstration — boutons AVANT la text_area
    st.markdown("<p style='font-size:0.8rem;color:#9ca3af;margin-bottom:6px;'>Cas de démonstration rapides :</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🫁 Syndrome respiratoire", use_container_width=True):
            st.session_state.demo_text = "Patient de 38 ans, fièvre à 38.5°C depuis 2 jours, toux sèche persistante, légère fatigue, pas de difficultés respiratoires."
            st.rerun()
    with c2:
        if st.button("⚠️ Red flags", use_container_width=True):
            st.session_state.demo_text = "Patient de 62 ans, douleur thoracique intense depuis 1h, difficultés respiratoires importantes, sueurs froides."
            st.rerun()
    with c3:
        if st.button("🌿 Cas bénin", use_container_width=True):
            st.session_state.demo_text = "Enfant de 9 ans, légère rhinite, nez qui coule depuis hier matin, pas de fièvre, mange normalement."
            st.rerun()

    st.markdown("")

    # text_area utilise demo_text comme valeur initiale (pas de key liée)
    patient_info = st.text_area(
        "Description du cas patient",
        value=st.session_state.demo_text,
        placeholder="Ex : Patient de 45 ans, fièvre depuis 3 jours, toux sèche persistante…",
        height=130,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Démarrer la consultation", use_container_width=True):
            if not patient_info.strip():
                st.warning("⚠️ Veuillez décrire le cas patient avant de continuer.")
            else:
                st.session_state.demo_text = ""  # reset
                st.session_state.patient_info = patient_info.strip()

                with st.spinner("Initialisation de la session…"):
                    session = api_post("/sessions/start", {})
                    st.session_state.thread_id = session["thread_id"]

                with st.spinner("Démarrage de la consultation…"):
                    data = api_post("/consultation/start", {
                        "thread_id": st.session_state.thread_id,
                        "patient_info": st.session_state.patient_info,
                    })
                    st.session_state.current_question = data.get("current_question") or QUESTIONS[0]
                    st.session_state.question_count = data.get("question_count", 0)
                    st.session_state.step = 2
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 — Questions / Réponses patient
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown("### 💬 Questions Cliniques")

    progress = st.session_state.question_count / 5
    st.markdown(f'<p class="progress-label">{st.session_state.question_count} / 5 questions complétées</p>', unsafe_allow_html=True)
    st.progress(progress)

    if st.session_state.patient_qa:
        st.markdown("**Réponses enregistrées :**")
        for i, qa in enumerate(st.session_state.patient_qa):
            st.markdown(f'<div class="q-bubble">Q{i+1} — {qa["question"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="a-bubble">↳ {qa["answer"]}</div>', unsafe_allow_html=True)

    if st.session_state.diagnostic_summary:
        st.markdown("---")
        st.markdown("#### ✅ Collecte terminée — Synthèse disponible")
        st.markdown('<div class="blue-card"><strong>Synthèse clinique préliminaire</strong><br><br>' + st.session_state.diagnostic_summary.replace('\n', '<br>') + '</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn-card"><strong>Recommandation intermédiaire</strong><br><br>' + (st.session_state.interim_care or "").replace('\n', '<br>') + '</div>', unsafe_allow_html=True)
        if st.button("👨‍⚕️ Passer à la revue médecin →", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

    elif st.session_state.question_count < 5:
        current_q = st.session_state.current_question or QUESTIONS[st.session_state.question_count]
        st.markdown(f'<div class="q-bubble" style="font-size:0.95rem;padding:12px 14px;">❓ <strong>Q{st.session_state.question_count + 1}</strong> — {current_q}</div>', unsafe_allow_html=True)

        answer = st.text_area(
            "Votre réponse",
            placeholder="Répondez à la question ci-dessus…",
            height=100,
            key=f"answer_{st.session_state.question_count}",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Envoyer la réponse →", use_container_width=True):
                if not answer.strip():
                    st.warning("⚠️ Veuillez saisir une réponse.")
                else:
                    st.session_state.patient_qa.append({
                        "question": current_q,
                        "answer": answer.strip(),
                    })
                    new_count = st.session_state.question_count + 1
                    st.session_state.question_count = new_count

                    with st.spinner("Envoi en cours…"):
                        data = api_post("/consultation/resume", {
                            "thread_id": st.session_state.thread_id,
                            "response": answer.strip(),
                            "response_type": "patient_answer",
                            "question_index": new_count - 1,
                        })

                    st.session_state.current_question = data.get("current_question")
                    if data.get("diagnostic_summary"):
                        st.session_state.diagnostic_summary = data["diagnostic_summary"]
                        st.session_state.interim_care = data.get("interim_care", "")

                    if new_count >= 5 and not st.session_state.diagnostic_summary:
                        qa_text = "\n".join([f"Q{i+1}: {q['question']}\nR: {q['answer']}" for i, q in enumerate(st.session_state.patient_qa)])
                        st.session_state.diagnostic_summary = f"Synthèse clinique préliminaire basée sur les {len(st.session_state.patient_qa)} réponses patient :\n\n{qa_text}"
                        st.session_state.interim_care = "Recommandation intermédiaire : repos, hydratation, surveillance des symptômes. Consultez un médecin si persistance.\n⚠️ Cette recommandation ne remplace pas une consultation médicale."

                    st.rerun()
        with col2:
            if st.button("↩ Retour", use_container_width=True):
                st.session_state.step = 1
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 — Revue Médecin (Human-in-the-Loop)
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown("### 👨‍⚕️ Revue Médecin Traitant")
    st.markdown('<div class="blue-card">⏸️ <strong>Human-in-the-Loop activé</strong> — Le workflow LangGraph est suspendu. Le médecin valide la synthèse et saisit sa conduite à tenir.</div>', unsafe_allow_html=True)

    with st.expander("📋 Synthèse clinique préliminaire", expanded=True):
        st.markdown(st.session_state.diagnostic_summary or "Non disponible")

    with st.expander("💊 Recommandation intermédiaire du système", expanded=False):
        st.markdown(st.session_state.interim_care or "Non disponible")

    st.markdown("---")
    st.markdown("#### ✍️ Traitement / Conduite à tenir")

    treatment = st.text_area(
        "Traitement ou conduite à tenir",
        placeholder="Ex : Paracétamol 1g toutes les 8h pendant 5 jours. Repos. Hydratation. Réévaluation dans 48h…",
        height=180,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✅ Valider et générer le rapport final", use_container_width=True):
            if not treatment.strip():
                st.warning("⚠️ Veuillez saisir la conduite à tenir.")
            else:
                st.session_state.physician_treatment = treatment.strip()
                with st.spinner("Génération du rapport final…"):
                    data = api_post("/consultation/resume", {
                        "thread_id": st.session_state.thread_id,
                        "response": treatment.strip(),
                        "response_type": "physician_treatment",
                    })

                final = data.get("final_report")
                if not final:
                    time.sleep(2)
                    try:
                        report_data = api_get(f"/consultation/{st.session_state.thread_id}/report")
                        final = report_data.get("final_report")
                    except Exception:
                        pass

                if not final:
                    from datetime import datetime
                    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
                    qa_lines = "\n".join([f"Q{i+1}: {q['question']}\n→ {q['answer']}" for i, q in enumerate(st.session_state.patient_qa)])
                    final = f"""RAPPORT D'ORIENTATION CLINIQUE PRÉLIMINAIRE
Date : {date_str}
Session : {st.session_state.thread_id}

═══════════════════════════════════════

INFORMATIONS PATIENT
{st.session_state.patient_info}

QUESTIONS / RÉPONSES CLINIQUES
{qa_lines}

SYNTHÈSE CLINIQUE PRÉLIMINAIRE
{st.session_state.diagnostic_summary}

RECOMMANDATION INTERMÉDIAIRE DU SYSTÈME
{st.session_state.interim_care}

DÉCISION DU MÉDECIN TRAITANT
{treatment.strip()}

═══════════════════════════════════════
⚠️  Ce système ne remplace pas une consultation médicale.
    Ce rapport est issu d'un exercice académique (LangGraph / FastAPI).
    Il ne constitue pas un acte médical."""

                st.session_state.final_report = final
                st.session_state.step = 4
                st.rerun()
    with col2:
        if st.button("↩ Retour", use_container_width=True):
            st.session_state.step = 2
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ÉTAPE 4 — Rapport Final
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown("### 📄 Rapport Final")
    st.success("✅ Consultation complétée — Rapport d'orientation clinique préliminaire généré")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Patient :** {st.session_state.patient_info[:80]}{'…' if len(st.session_state.patient_info) > 80 else ''}")
        st.markdown(f"**Questions posées :** {st.session_state.question_count}/5")
    with col2:
        st.markdown(f"**Session :** `{(st.session_state.thread_id or '')[:20]}…`")
        st.markdown("**Statut :** Rapport validé par médecin traitant ✓")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("🔬 Synthèse clinique préliminaire", expanded=False):
            st.markdown(st.session_state.diagnostic_summary or "—")
        with st.expander("💊 Recommandation intermédiaire", expanded=False):
            st.markdown(st.session_state.interim_care or "—")
    with col_b:
        with st.expander("👨‍⚕️ Décision médecin traitant", expanded=True):
            st.markdown(st.session_state.physician_treatment or "—")

    st.markdown("---")
    st.markdown("#### 📋 Rapport complet")
    st.markdown(f'<div class="report-card">{st.session_state.final_report or ""}</div>', unsafe_allow_html=True)

    st.markdown("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.final_report:
            st.download_button(
                label="⬇️ Télécharger",
                data=st.session_state.final_report,
                file_name=f"rapport_{(st.session_state.thread_id or 'local')[:8]}.txt",
                mime="text/plain",
                use_container_width=True,
            )
    with col2:
        if st.button("🔄 Nouvelle consultation", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col3:
        if st.button("🔗 Rapport via API", use_container_width=True):
            if st.session_state.thread_id:
                with st.spinner("Récupération…"):
                    try:
                        data = api_get(f"/consultation/{st.session_state.thread_id}/report")
                        st.session_state.final_report = data.get("final_report", st.session_state.final_report)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")


# ── Disclaimer ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
    ⚠️ Ce système ne remplace pas une consultation médicale ·
    Exercice académique LangGraph + LangChain + FastAPI ·
    Aucun diagnostic définitif n'est fourni
</div>
""", unsafe_allow_html=True)