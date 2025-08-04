"""
Service pour gérer le diagnostic par étapes
"""
import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone

from ..models import (
    SessionDiagnostic, QuestionDiagnostic, TemplateDiagnostic,
    DiagnosticSysteme, HistoriqueDiagnostic, ReponseDiagnostic
)
from ..diagnostic_engine import DiagnosticSystemeEngine

logger = logging.getLogger(__name__)


class DiagnosticEtapesService:
    """Service pour gérer le diagnostic par étapes avec un plan structuré"""

    def __init__(self, session: SessionDiagnostic, template_id: Optional[int] = None):
        self.session = session
        self.template_id = template_id

    def generer_plan_etapes(self) -> List[Dict[str, Any]]:
        """Génère un plan d'étapes pour le diagnostic"""
        plan_etapes = []

        # Étape 1: Diagnostic système automatique
        plan_etapes.append({
            'id': 'diagnostic_systeme',
            'type': 'diagnostic_automatique',
            'titre': 'Analyse automatique du système',
            'description': 'Le système analyse automatiquement votre ordinateur pour détecter les problèmes courants',
            'icone': 'computer',
            'temps_estime': 30,  # en secondes
            'obligatoire': True,
            'parametres': {
                'types_diagnostic': ['memoire', 'disque', 'reseau', 'cpu', 'services']
            }
        })

        # Étape 2: Questions de pré-filtrage
        plan_etapes.append({
            'id': 'questions_prefiltrage',
            'type': 'questions',
            'titre': 'Questions préliminaires',
            'description': 'Quelques questions rapides pour orienter le diagnostic',
            'icone': 'question',
            'temps_estime': 60,
            'obligatoire': True,
            'parametres': {
                'questions_ids': self._obtenir_questions_prefiltrage(),
                'max_questions': 3
            }
        })

        # Étape 3: Diagnostic approfondi basé sur la catégorie
        plan_etapes.append({
            'id': 'diagnostic_approfondi',
            'type': 'questions_avancees',
            'titre': 'Diagnostic approfondi',
            'description': f'Questions spécialisées pour {self.session.categorie.nom_categorie}',
            'icone': 'search',
            'temps_estime': 180,
            'obligatoire': False,
            'parametres': {
                'categorie_id': self.session.categorie.id,
                'adapter_selon_resultats': True
            }
        })

        # Étape 4: Tests interactifs (optionnel)
        plan_etapes.append({
            'id': 'tests_interactifs',
            'type': 'tests',
            'titre': 'Tests interactifs',
            'description': 'Tests guidés pour valider les solutions',
            'icone': 'play',
            'temps_estime': 120,
            'obligatoire': False,
            'parametres': {
                'selon_probleme': True
            }
        })

        # Étape 5: Synthèse et recommandations
        plan_etapes.append({
            'id': 'synthese',
            'type': 'synthese',
            'titre': 'Résultats et recommandations',
            'description': 'Synthèse du diagnostic et plan d\'action',
            'icone': 'report',
            'temps_estime': 60,
            'obligatoire': True,
            'parametres': {
                'generer_recommandations': True,
                'calculer_priorite': True
            }
        })

        # Si un template est spécifié, adapter le plan
        if self.template_id:
            plan_etapes = self._adapter_plan_avec_template(plan_etapes)

        return plan_etapes

    def _obtenir_questions_prefiltrage(self) -> List[int]:
        """Obtient les questions de pré-filtrage pour la catégorie"""
        # Questions critiques de la catégorie, limitées à 3
        questions = QuestionDiagnostic.objects.filter(
            categorie=self.session.categorie,
            est_critique=True,
            actif=True
        ).order_by('ordre')[:3]

        return [q.id for q in questions]

    def _adapter_plan_avec_template(self, plan_etapes: List[Dict]) -> List[Dict]:
        """Adapte le plan d'étapes selon un template"""
        try:
            template = TemplateDiagnostic.objects.get(id=self.template_id, est_actif=True)

            # Modifier l'étape de diagnostic approfondi selon le template
            for etape in plan_etapes:
                if etape['id'] == 'diagnostic_approfondi':
                    etape['titre'] = f'Diagnostic: {template.nom}'
                    etape['description'] = template.description or etape['description']
                    etape['parametres']['template_id'] = template.id

        except TemplateDiagnostic.DoesNotExist:
            logger.warning(f"Template {self.template_id} non trouvé")

        return plan_etapes

    def executer_etape_actuelle(self, donnees_entree: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'étape actuelle du diagnostic"""
        plan_etapes = self.session.donnees_supplementaires.get('plan_etapes', [])
        etape_actuelle_idx = self.session.donnees_supplementaires.get('etape_actuelle', 0)
        etapes_completees = self.session.donnees_supplementaires.get('etapes_completees', [])

        if etape_actuelle_idx >= len(plan_etapes):
            return {
                'success': False,
                'error': 'Aucune étape à exécuter'
            }

        etape_actuelle = plan_etapes[etape_actuelle_idx]

        try:
            # Exécuter l'étape selon son type
            if etape_actuelle['type'] == 'diagnostic_automatique':
                resultat = self._executer_diagnostic_automatique(etape_actuelle, donnees_entree)
            elif etape_actuelle['type'] == 'questions':
                resultat = self._executer_questions(etape_actuelle, donnees_entree)
            elif etape_actuelle['type'] == 'questions_avancees':
                resultat = self._executer_questions_avancees(etape_actuelle, donnees_entree)
            elif etape_actuelle['type'] == 'tests':
                resultat = self._executer_tests_interactifs(etape_actuelle, donnees_entree)
            elif etape_actuelle['type'] == 'synthese':
                resultat = self._executer_synthese(etape_actuelle, donnees_entree)
            else:
                return {
                    'success': False,
                    'error': f'Type d\'étape non supporté: {etape_actuelle["type"]}'
                }

            # Marquer l'étape comme complétée
            if resultat['success']:
                etapes_completees.append({
                    'etape_id': etape_actuelle['id'],
                    'date_completion': timezone.now().isoformat(),
                    'resultats': resultat.get('donnees', {})
                })

                # Passer à l'étape suivante
                nouvelle_etape_idx = etape_actuelle_idx + 1

                # Mettre à jour la session
                self.session.donnees_supplementaires['etapes_completees'] = etapes_completees
                self.session.donnees_supplementaires['etape_actuelle'] = nouvelle_etape_idx
                self.session.save()

                # Enregistrer dans l'historique
                HistoriqueDiagnostic.objects.create(
                    session=self.session,
                    action='etape_completee',
                    utilisateur=self.session.utilisateur,
                    details={
                        'etape_id': etape_actuelle['id'],
                        'etape_titre': etape_actuelle['titre'],
                        'resultats': resultat.get('donnees', {})
                    }
                )

                # Préparer la réponse
                progression = {
                    'etape_courante': nouvelle_etape_idx + 1,
                    'total_etapes': len(plan_etapes),
                    'pourcentage': round((len(etapes_completees) / len(plan_etapes)) * 100)
                }

                prochaine_etape = None
                diagnostic_termine = False

                if nouvelle_etape_idx < len(plan_etapes):
                    prochaine_etape = plan_etapes[nouvelle_etape_idx]
                else:
                    # Diagnostic terminé
                    diagnostic_termine = True
                    self._finaliser_diagnostic()

                return {
                    'success': True,
                    'etape_completee': etape_actuelle,
                    'resultat': resultat,
                    'prochaine_etape': prochaine_etape,
                    'progression': progression,
                    'diagnostic_termine': diagnostic_termine
                }
            else:
                return resultat

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'étape {etape_actuelle['id']}: {e}")
            return {
                'success': False,
                'error': f'Erreur lors de l\'exécution: {str(e)}'
            }

    def _executer_diagnostic_automatique(self, etape: Dict, donnees: Dict) -> Dict[str, Any]:
        """Exécute le diagnostic système automatique"""
        try:
            diagnostic_engine = DiagnosticSystemeEngine(self.session)
            resultats = diagnostic_engine.executer_diagnostic_complet()

            # Analyser les résultats pour détecter les problèmes
            problemes_detectes = []
            score_global = 0

            for type_diag, resultat in resultats.items():
                if resultat['statut'] == 'erreur':
                    problemes_detectes.append({
                        'type': type_diag,
                        'message': resultat['message'],
                        'severite': 'critique'
                    })
                    score_global += 10
                elif resultat['statut'] == 'avertissement':
                    problemes_detectes.append({
                        'type': type_diag,
                        'message': resultat['message'],
                        'severite': 'moyen'
                    })
                    score_global += 5

            return {
                'success': True,
                'donnees': {
                    'resultats_diagnostics': resultats,
                    'problemes_detectes': problemes_detectes,
                    'score_global': score_global,
                    'temps_execution': 30
                },
                'message': f'{len(problemes_detectes)} problème(s) détecté(s)' if problemes_detectes else 'Système sain'
            }

        except Exception as e:
            logger.error(f"Erreur diagnostic automatique: {e}")
            return {
                'success': False,
                'error': f'Erreur lors du diagnostic automatique: {str(e)}'
            }

    def _executer_questions(self, etape: Dict, donnees: Dict) -> Dict[str, Any]:
        """Exécute une série de questions"""
        try:
            questions_ids = etape['parametres'].get('questions_ids', [])
            reponses = donnees.get('reponses', {})

            if not reponses:
                return {
                    'success': False,
                    'error': 'Aucune réponse fournie'
                }

            score_total = 0
            reponses_enregistrees = []

            for question_id, reponse_data in reponses.items():
                try:
                    question = QuestionDiagnostic.objects.get(id=question_id)

                    # Créer la réponse
                    reponse = ReponseDiagnostic.objects.create(
                        session=self.session,
                        question=question,
                        reponse_texte=reponse_data.get('texte', ''),
                        temps_passe=reponse_data.get('temps_passe', 0)
                    )

                    # Ajouter les choix sélectionnés
                    if 'choix_ids' in reponse_data:
                        from ..models import ChoixReponse
                        choix = ChoixReponse.objects.filter(id__in=reponse_data['choix_ids'])
                        reponse.choix_selectionnes.set(choix)
                        score_total += sum(c.score_criticite for c in choix)

                    reponse.score_criticite = score_total
                    reponse.save()

                    reponses_enregistrees.append({
                        'question_id': question_id,
                        'reponse_id': reponse.id,
                        'score': reponse.score_criticite
                    })

                except QuestionDiagnostic.DoesNotExist:
                    logger.warning(f"Question {question_id} non trouvée")

            return {
                'success': True,
                'donnees': {
                    'reponses_enregistrees': reponses_enregistrees,
                    'score_etape': score_total,
                    'nombre_questions': len(reponses_enregistrees)
                },
                'message': f'{len(reponses_enregistrees)} réponse(s) enregistrée(s)'
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution des questions: {e}")
            return {
                'success': False,
                'error': f'Erreur lors du traitement des questions: {str(e)}'
            }

    def _executer_questions_avancees(self, etape: Dict, donnees: Dict) -> Dict[str, Any]:
        """Exécute les questions avancées basées sur les résultats précédents"""
        # Adapter les questions selon les résultats des étapes précédentes
        etapes_completees = self.session.donnees_supplementaires.get('etapes_completees', [])

        # Analyser les problèmes détectés pour adapter les questions
        questions_adaptees = self._adapter_questions_selon_problemes(etapes_completees)

        # Utiliser la même logique que _executer_questions mais avec les questions adaptées
        etape['parametres']['questions_ids'] = questions_adaptees
        return self._executer_questions(etape, donnees)

    def _executer_tests_interactifs(self, etape: Dict, donnees: Dict) -> Dict[str, Any]:
        """Exécute des tests interactifs"""
        try:
            resultats_tests = donnees.get('resultats_tests', {})

            # Traiter les résultats des tests
            tests_reussis = 0
            tests_total = len(resultats_tests)

            for test_id, resultat in resultats_tests.items():
                if resultat.get('succes', False):
                    tests_reussis += 1

            return {
                'success': True,
                'donnees': {
                    'tests_reussis': tests_reussis,
                    'tests_total': tests_total,
                    'taux_succes': (tests_reussis / tests_total * 100) if tests_total > 0 else 0,
                    'resultats_detailles': resultats_tests
                },
                'message': f'{tests_reussis}/{tests_total} tests réussis'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors des tests: {str(e)}'
            }

    def _executer_synthese(self, etape: Dict, donnees: Dict) -> Dict[str, Any]:
        """Génère la synthèse finale du diagnostic"""
        try:
            from ..diagnostic_engine import ArbreDecisionEngine

            # Calculer le score total et la priorité
            arbre_engine = ArbreDecisionEngine(self.session)
            priorite, score_total = arbre_engine.calculer_priorite_estimee()
            recommandations = arbre_engine.generer_recommandations()

            # Analyser toutes les étapes pour créer un résumé
            etapes_completees = self.session.donnees_supplementaires.get('etapes_completees', [])

            resume_etapes = []
            for etape_completee in etapes_completees:
                resume_etapes.append({
                    'etape': etape_completee['etape_id'],
                    'statut': 'completee',
                    'problemes_detectes': len(etape_completee.get('resultats', {}).get('problemes_detectes', []))
                })

            # Mettre à jour la session
            self.session.score_criticite_total = score_total
            self.session.priorite_estimee = priorite
            self.session.recommandations = recommandations
            self.session.save()

            return {
                'success': True,
                'donnees': {
                    'priorite_finale': priorite,
                    'score_total': score_total,
                    'recommandations': recommandations,
                    'resume_etapes': resume_etapes,
                    'duree_totale': self.session.temps_total_passe
                },
                'message': 'Diagnostic terminé avec succès'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la synthèse: {str(e)}'
            }

    def _adapter_questions_selon_problemes(self, etapes_completees: List[Dict]) -> List[int]:
        """Adapte les questions selon les problèmes détectés dans les étapes précédentes"""
        questions_ids = []

        # Analyser les problèmes détectés
        for etape in etapes_completees:
            if etape['etape_id'] == 'diagnostic_systeme':
                problemes = etape.get('resultats', {}).get('problemes_detectes', [])

                # Selon les types de problèmes, sélectionner des questions spécifiques
                for probleme in problemes:
                    if probleme['type'] == 'memoire':
                        questions_memoire = QuestionDiagnostic.objects.filter(
                            categorie=self.session.categorie,
                            tags__contains=['memoire'],
                            actif=True
                        ).values_list('id', flat=True)[:2]
                        questions_ids.extend(questions_memoire)

                    elif probleme['type'] == 'reseau':
                        questions_reseau = QuestionDiagnostic.objects.filter(
                            categorie=self.session.categorie,
                            tags__contains=['reseau'],
                            actif=True
                        ).values_list('id', flat=True)[:2]
                        questions_ids.extend(questions_reseau)

        # Si aucun problème spécifique, prendre les questions par défaut de la catégorie
        if not questions_ids:
            questions_ids = list(QuestionDiagnostic.objects.filter(
                categorie=self.session.categorie,
                actif=True
            ).order_by('ordre').values_list('id', flat=True)[:5])

        return questions_ids

    def _finaliser_diagnostic(self):
        """Finalise le diagnostic et met à jour le statut de la session"""
        self.session.statut = 'complete'
        self.session.date_completion = timezone.now()
        self.session.save()

        # Enregistrer dans l'historique
        HistoriqueDiagnostic.objects.create(
            session=self.session,
            action='completion',
            utilisateur=self.session.utilisateur,
            details={
                'diagnostic_par_etapes': True,
                'etapes_completees': len(self.session.donnees_supplementaires.get('etapes_completees', [])),
                'score_final': self.session.score_criticite_total,
                'priorite_finale': self.session.priorite_estimee
            }
        )
