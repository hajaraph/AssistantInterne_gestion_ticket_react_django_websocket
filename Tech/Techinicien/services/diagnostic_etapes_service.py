"""
Service pour gérer le diagnostic par étapes
Permet de guider l'utilisateur à travers un processus de diagnostic structuré
"""

import json
import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone

from ..models import (
    SessionDiagnostic, QuestionDiagnostic, ReponseDiagnostic,
    DiagnosticSysteme, TemplateDiagnostic, TemplateQuestion,
    HistoriqueDiagnostic, ChoixReponse
)
from ..diagnostic_engine import DiagnosticSystemeEngine, ArbreDecisionEngine

logger = logging.getLogger(__name__)


class DiagnosticEtapesService:
    """Service pour gérer le diagnostic par étapes"""

    def __init__(self, session: SessionDiagnostic, template_id: Optional[int] = None):
        self.session = session
        self.template_id = template_id
        self.template = self._obtenir_template()

    def _obtenir_template(self) -> Optional[TemplateDiagnostic]:
        """Obtient le template spécifié ou le template par défaut pour la catégorie"""
        try:
            if self.template_id:
                return TemplateDiagnostic.objects.get(
                    id=self.template_id,
                    est_actif=True
                )
            else:
                return TemplateDiagnostic.objects.filter(
                    categorie=self.session.categorie,
                    est_actif=True
                ).first()
        except TemplateDiagnostic.DoesNotExist:
            return None

    def generer_plan_etapes(self) -> List[Dict[str, Any]]:
        """Génère le plan d'étapes pour le diagnostic"""
        etapes = []

        # Étape 1: Diagnostic automatique du système
        etapes.append({
            'id': 'diagnostic_systeme',
            'type': 'diagnostic_automatique',
            'titre': 'Analyse automatique du système',
            'description': 'Analyse des performances et de l\'état de votre ordinateur',
            'icone': 'computer',
            'temps_estime': 30,
            'obligatoire': True,
            'parametres': {
                'types_diagnostic': ['memoire', 'disque', 'reseau', 'cpu', 'performance']
            }
        })

        # Étape 2: Questions de diagnostic si template disponible
        if self.template:
            questions = self._obtenir_questions_template()
            if questions:
                etapes.append({
                    'id': 'questionnaire',
                    'type': 'questionnaire_interactif',
                    'titre': f'Questionnaire - {self.session.categorie.nom_categorie}',
                    'description': 'Répondez aux questions pour affiner le diagnostic',
                    'icone': 'question-circle',
                    'temps_estime': len(questions) * 30,
                    'obligatoire': True,
                    'parametres': {
                        'questions': questions,
                        'mode': 'adaptatif' if not self.template.est_lineaire else 'lineaire'
                    }
                })
        else:
            # Questions par défaut de la catégorie
            questions_defaut = QuestionDiagnostic.objects.filter(
                categorie=self.session.categorie,
                actif=True,
                question_parent__isnull=True
            ).order_by('ordre')[:5]

            if questions_defaut.exists():
                etapes.append({
                    'id': 'questionnaire',
                    'type': 'questionnaire_simple',
                    'titre': 'Questions de diagnostic',
                    'description': 'Questions rapides pour mieux comprendre votre problème',
                    'icone': 'question-circle',
                    'temps_estime': questions_defaut.count() * 30,
                    'obligatoire': True,
                    'parametres': {
                        'questions': [self._serialiser_question(q) for q in questions_defaut]
                    }
                })

        # Étape 3: Analyse et recommandations
        etapes.append({
            'id': 'analyse_recommandations',
            'type': 'analyse_resultats',
            'titre': 'Analyse et recommandations',
            'description': 'Analyse des résultats et génération des recommandations',
            'icone': 'chart-line',
            'temps_estime': 15,
            'obligatoire': True,
            'parametres': {
                'generer_recommandations': True,
                'calculer_priorite': True
            }
        })

        # Étape 4: Actions recommandées
        etapes.append({
            'id': 'actions_recommandees',
            'type': 'actions_utilisateur',
            'titre': 'Actions recommandées',
            'description': 'Actions que vous pouvez essayer avant de créer un ticket',
            'icone': 'tools',
            'temps_estime': 60,
            'obligatoire': False,
            'parametres': {
                'actions_automatiques': True,
                'guides_pas_a_pas': True
            }
        })

        # Étape 5: Décision finale
        etapes.append({
            'id': 'decision_finale',
            'type': 'decision',
            'titre': 'Que souhaitez-vous faire ?',
            'description': 'Choisissez la prochaine action selon les résultats du diagnostic',
            'icone': 'decision',
            'temps_estime': 0,
            'obligatoire': True,
            'parametres': {
                'options': [
                    'probleme_resolu',
                    'creer_ticket_auto',
                    'creer_ticket_manuel',
                    'contacter_support'
                ]
            }
        })

        return etapes

    def _obtenir_questions_template(self) -> List[Dict[str, Any]]:
        """Obtient les questions du template"""
        if not self.template:
            return []

        questions_template = self.template.template_questions.filter(
            question__actif=True
        ).order_by('ordre')

        return [self._serialiser_question_template(qt) for qt in questions_template]

    def _serialiser_question(self, question: QuestionDiagnostic) -> Dict[str, Any]:
        """Sérialise une question pour l'étape"""
        return {
            'id': question.id,
            'titre': question.titre,
            'description': question.description,
            'type': question.type_question,
            'est_critique': question.est_critique,
            'choix': [
                {
                    'id': choix.id,
                    'texte': choix.texte,
                    'valeur': choix.valeur,
                    'score': choix.score_criticite
                }
                for choix in question.choix_reponses.all().order_by('ordre')
            ]
        }

    def _serialiser_question_template(self, question_template: TemplateQuestion) -> Dict[str, Any]:
        """Sérialise une question de template pour l'étape"""
        question = question_template.question
        return {
            'id': question.id,
            'titre': question.titre,
            'description': question.description,
            'type': question.type_question,
            'est_critique': question.est_critique,
            'ordre_template': question_template.ordre,
            'conditions': question_template.condition_affichage,
            'choix': [
                {
                    'id': choix.id,
                    'texte': choix.texte,
                    'valeur': choix.valeur,
                    'score': choix.score_criticite
                }
                for choix in question.choix_reponses.all().order_by('ordre')
            ]
        }

    def executer_etape_actuelle(self, donnees_etape: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'étape actuelle du diagnostic"""
        try:
            plan_etapes = self.session.donnees_supplementaires.get('plan_etapes', [])
            etape_actuelle_idx = self.session.donnees_supplementaires.get('etape_actuelle', 0)
            etapes_completees = self.session.donnees_supplementaires.get('etapes_completees', [])

            if etape_actuelle_idx >= len(plan_etapes):
                return {
                    'success': False,
                    'error': 'Aucune étape à exécuter'
                }

            etape_actuelle = plan_etapes[etape_actuelle_idx]
            type_etape = etape_actuelle['type']

            # Exécuter selon le type d'étape
            if type_etape == 'diagnostic_automatique':
                resultat = self._executer_diagnostic_automatique(etape_actuelle, donnees_etape)
            elif type_etape in ['questionnaire_interactif', 'questionnaire_simple']:
                resultat = self._executer_questionnaire(etape_actuelle, donnees_etape)
            elif type_etape == 'analyse_resultats':
                resultat = self._executer_analyse_resultats(etape_actuelle, donnees_etape)
            elif type_etape == 'actions_utilisateur':
                resultat = self._executer_actions_utilisateur(etape_actuelle, donnees_etape)
            elif type_etape == 'decision':
                resultat = self._executer_decision(etape_actuelle, donnees_etape)
            else:
                return {
                    'success': False,
                    'error': f'Type d\'étape non supporté: {type_etape}'
                }

            if resultat['success']:
                # Marquer l'étape comme complétée
                etapes_completees.append({
                    'etape_id': etape_actuelle['id'],
                    'date_completion': timezone.now().isoformat(),
                    'resultat': resultat.get('resultat_etape', {})
                })

                # Passer à l'étape suivante
                nouvelle_etape_idx = etape_actuelle_idx + 1

                # Mettre à jour la session
                self.session.donnees_supplementaires['etape_actuelle'] = nouvelle_etape_idx
                self.session.donnees_supplementaires['etapes_completees'] = etapes_completees
                self.session.save()

                # Prochaine étape
                prochaine_etape = None
                if nouvelle_etape_idx < len(plan_etapes):
                    prochaine_etape = plan_etapes[nouvelle_etape_idx]

                # Calculer la progression
                progression = {
                    'etape_courante': nouvelle_etape_idx + 1,
                    'total_etapes': len(plan_etapes),
                    'pourcentage': round((len(etapes_completees) / len(plan_etapes)) * 100)
                }

                return {
                    'success': True,
                    'etape_completee': etape_actuelle,
                    'resultat': resultat,
                    'prochaine_etape': prochaine_etape,
                    'progression': progression,
                    'diagnostic_termine': nouvelle_etape_idx >= len(plan_etapes)
                }

            return resultat

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'étape: {e}")
            return {
                'success': False,
                'error': f'Erreur lors de l\'exécution: {str(e)}'
            }

    def _executer_diagnostic_automatique(self, etape: Dict[str, Any], donnees: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute le diagnostic automatique du système"""
        try:
            engine = DiagnosticSystemeEngine(self.session)
            resultats = engine.executer_diagnostic_complet()

            return {
                'success': True,
                'resultat_etape': {
                    'type': 'diagnostic_automatique',
                    'diagnostics': resultats,
                    'resume': self._generer_resume_diagnostic(resultats)
                }
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic automatique: {e}")
            return {
                'success': False,
                'error': f'Erreur lors du diagnostic automatique: {str(e)}'
            }

    def _executer_questionnaire(self, etape: Dict[str, Any], donnees: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'étape questionnaire"""
        try:
            reponses = donnees.get('reponses', {})

            for question_id, reponse_data in reponses.items():
                # Sauvegarder la réponse
                question = QuestionDiagnostic.objects.get(id=question_id)

                # Créer ou récupérer la réponse
                reponse, created = ReponseDiagnostic.objects.get_or_create(
                    session=self.session,
                    question=question,
                    defaults={
                        'reponse_texte': reponse_data.get('texte', ''),
                        'temps_passe': reponse_data.get('temps_passe', 0),
                        'est_incertain': reponse_data.get('est_incertain', False),
                        'commentaire': reponse_data.get('commentaire', '')
                    }
                )

                # Si la réponse existe déjà, la mettre à jour
                if not created:
                    reponse.reponse_texte = reponse_data.get('texte', '')
                    reponse.temps_passe = reponse_data.get('temps_passe', 0)
                    reponse.est_incertain = reponse_data.get('est_incertain', False)
                    reponse.commentaire = reponse_data.get('commentaire', '')
                    reponse.save()

                # Gérer les choix sélectionnés avec la nouvelle approche ForeignKey
                choix_ids = reponse_data.get('choix_ids', [])
                if choix_ids:
                    # Vider les anciens choix
                    reponse.vider_choix()

                    # Ajouter les nouveaux choix un par un
                    choix_objets = ChoixReponse.objects.filter(id__in=choix_ids)
                    for choix in choix_objets:
                        reponse.ajouter_choix(choix)

            # Mettre à jour le score total de la session
            score_total = sum(r.score_criticite for r in self.session.reponses.all())
            self.session.score_criticite_total = score_total
            self.session.save()

            return {
                'success': True,
                'resultat_etape': {
                    'type': 'questionnaire',
                    'nombre_reponses': len(reponses),
                    'score_total': score_total
                }
            }

        except Exception as e:
            logger.error(f"Erreur questionnaire: {e}")
            return {
                'success': False,
                'error': f'Erreur lors du questionnaire: {str(e)}'
            }

    def _executer_analyse_resultats(self, etape: Dict[str, Any], donnees: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'analyse des résultats et génère les recommandations"""
        try:
            engine = ArbreDecisionEngine(self.session)

            # Calculer la priorité estimée
            priorite, score_total = engine.calculer_priorite_estimee()

            # Générer les recommandations
            recommandations = engine.generer_recommandations()

            # Mettre à jour la session
            self.session.priorite_estimee = priorite
            self.session.score_criticite_total = score_total
            self.session.recommandations = recommandations
            self.session.save()

            return {
                'success': True,
                'resultat_etape': {
                    'type': 'analyse',
                    'priorite_estimee': priorite,
                    'score_total': score_total,
                    'recommandations': recommandations,
                    'niveau_criticite': self._determiner_niveau_criticite(priorite, score_total)
                }
            }

        except Exception as e:
            logger.error(f"Erreur analyse: {e}")
            return {
                'success': False,
                'error': f'Erreur lors de l\'analyse: {str(e)}'
            }

    def _executer_actions_utilisateur(self, etape: Dict[str, Any], donnees: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute les actions recommandées à l'utilisateur"""
        actions_effectuees = donnees.get('actions_effectuees', [])

        # Enregistrer les actions dans l'historique
        HistoriqueDiagnostic.objects.create(
            session=self.session,
            action='systeme',
            utilisateur=self.session.utilisateur,
            details={
                'actions_effectuees': actions_effectuees,
                'etape': 'actions_utilisateur'
            }
        )

        return {
            'success': True,
            'resultat_etape': {
                'type': 'actions',
                'actions_effectuees': actions_effectuees,
                'nombre_actions': len(actions_effectuees)
            }
        }

    def _executer_decision(self, etape: Dict[str, Any], donnees: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'étape de décision finale"""
        decision = donnees.get('decision')

        if not decision:
            return {
                'success': False,
                'error': 'Aucune décision fournie'
            }

        # Marquer la session comme complète
        self.session.statut = 'complete'
        self.session.date_completion = timezone.now()
        self.session.save()

        return {
            'success': True,
            'resultat_etape': {
                'type': 'decision',
                'decision': decision,
                'session_complete': True
            }
        }

    def _generer_resume_diagnostic(self, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un résumé des diagnostics"""
        problemes = []
        avertissements = []
        ok_count = 0

        for type_diag, resultat in diagnostics.items():
            if resultat['statut'] == 'erreur':
                problemes.append({
                    'type': type_diag,
                    'message': resultat['message']
                })
            elif resultat['statut'] == 'avertissement':
                avertissements.append({
                    'type': type_diag,
                    'message': resultat['message']
                })
            else:
                ok_count += 1

        return {
            'problemes_critiques': len(problemes),
            'avertissements': len(avertissements),
            'tests_ok': ok_count,
            'total_tests': len(diagnostics),
            'details_problemes': problemes,
            'details_avertissements': avertissements
        }

    def _determiner_niveau_criticite(self, priorite: str, score: int) -> str:
        """Détermine le niveau de criticité pour l'affichage"""
        if priorite == 'critique':
            return 'critique'
        elif priorite == 'urgent':
            return 'urgent'
        elif priorite == 'normal':
            return 'normal'
        else:
            return 'faible'
