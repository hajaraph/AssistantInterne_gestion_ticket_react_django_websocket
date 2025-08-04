"""
Moteur de diagnostic automatique pour analyser l'état du système
et guider l'utilisateur à travers un questionnaire intelligent
"""

import json
import logging
import platform
import psutil
import subprocess
import socket
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from django.conf import settings
from .models import (
    SessionDiagnostic, QuestionDiagnostic, ReponseDiagnostic,
    DiagnosticSysteme, RegleDiagnostic, ChoixReponse, TemplateDiagnostic,
    TemplateQuestion, HistoriqueDiagnostic
)

logger = logging.getLogger(__name__)


class DiagnosticSystemeEngine:
    """Moteur de diagnostic automatique du système"""

    def __init__(self, session: SessionDiagnostic):
        self.session = session
        self.resultats = {}
        self.debut_diagnostic = time.time()

    def executer_diagnostic_complet(self) -> Dict[str, Any]:
        """Exécute un diagnostic complet du système"""
        # Enregistrer le début du diagnostic dans l'historique
        HistoriqueDiagnostic.objects.create(
            session=self.session,
            action='systeme',
            utilisateur=self.session.utilisateur,
            details={'action': 'debut_diagnostic_systeme'}
        )

        diagnostics = {
            'memoire': self.diagnostic_memoire(),
            'disque': self.diagnostic_disque(),
            'reseau': self.diagnostic_reseau(),
            'cpu': self.diagnostic_cpu(),
            'services': self.diagnostic_services_windows(),
            'logiciels': self.diagnostic_logiciels(),
            'securite': self.diagnostic_securite(),
            'performance': self.diagnostic_performance(),
            'systeme': self.diagnostic_systeme_os()
        }

        # Sauvegarder les résultats dans la base de données
        for type_diag, resultat in diagnostics.items():
            self.sauvegarder_diagnostic(type_diag, resultat)

        # Mettre à jour les données supplémentaires de la session
        self.session.diagnostic_automatique = diagnostics
        self.session.save(update_fields=['diagnostic_automatique'])

        return diagnostics

    @staticmethod
    def diagnostic_memoire() -> Dict[str, Any]:
        """Diagnostic de la mémoire système"""
        try:
            memoire = psutil.virtual_memory()
            resultat = {
                'total_gb': round(memoire.total / (1024**3), 2),
                'disponible_gb': round(memoire.available / (1024**3), 2),
                'utilise_pourcentage': memoire.percent,
                'libre_gb': round(memoire.free / (1024**3), 2)
            }

            # Déterminer le statut
            if memoire.percent > 90:
                statut = 'erreur'
                message = f"Mémoire critique: {memoire.percent}% utilisée"
            elif memoire.percent > 80:
                statut = 'avertissement'
                message = f"Mémoire élevée: {memoire.percent}% utilisée"
            else:
                statut = 'ok'
                message = f"Mémoire normale: {memoire.percent}% utilisée"

            return {
                'statut': statut,
                'message': message,
                'details': resultat
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic mémoire: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser la mémoire: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_disque() -> Dict[str, Any]:
        """Diagnostic de l'espace disque"""
        try:
            disques = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disque_info = {
                        'mountpoint': partition.mountpoint,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'utilise_gb': round(usage.used / (1024**3), 2),
                        'libre_gb': round(usage.free / (1024**3), 2),
                        'pourcentage': round((usage.used / usage.total) * 100, 2)
                    }
                    disques.append(disque_info)
                except PermissionError:
                    continue

            # Trouver le disque le plus plein
            max_usage = max(disques, key=lambda x: x['pourcentage']) if disques else None

            if max_usage and max_usage['pourcentage'] > 90:
                statut = 'erreur'
                message = f"Disque {max_usage['mountpoint']} critique: {max_usage['pourcentage']}% plein"
            elif max_usage and max_usage['pourcentage'] > 80:
                statut = 'avertissement'
                message = f"Disque {max_usage['mountpoint']} élevé: {max_usage['pourcentage']}% plein"
            else:
                statut = 'ok'
                message = "Espace disque normal"

            return {
                'statut': statut,
                'message': message,
                'details': {'disques': disques}
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic disque: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser les disques: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_reseau() -> Dict[str, Any]:
        """Diagnostic de la connectivité réseau"""
        try:
            resultats = {}

            # Test de connectivité Internet
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                resultats['internet'] = True
            except OSError:
                resultats['internet'] = False

            # Informations sur les interfaces réseau
            interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append({
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })

            resultats['interfaces'] = interfaces

            # Statistiques réseau
            stats = psutil.net_io_counters()
            resultats['statistiques'] = {
                'bytes_envoyes': stats.bytes_sent,
                'bytes_recus': stats.bytes_recv,
                'paquets_envoyes': stats.packets_sent,
                'paquets_recus': stats.packets_recv
            }

            if not resultats['internet']:
                statut = 'erreur'
                message = "Pas de connectivité Internet"
            elif not interfaces:
                statut = 'avertissement'
                message = "Aucune interface réseau active détectée"
            else:
                statut = 'ok'
                message = "Connectivité réseau normale"

            return {
                'statut': statut,
                'message': message,
                'details': resultats
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic réseau: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser le réseau: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_cpu() -> Dict[str, Any]:
        """Diagnostic du processeur"""
        try:
            # Utilisation CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            resultats = {
                'utilisation_pourcentage': cpu_percent,
                'nombre_coeurs': cpu_count,
                'frequence_mhz': cpu_freq.current if cpu_freq else 'Non disponible',
                'charge_moyenne': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else 'Non disponible'
            }

            if cpu_percent > 90:
                statut = 'erreur'
                message = f"CPU critique: {cpu_percent}% d'utilisation"
            elif cpu_percent > 80:
                statut = 'avertissement'
                message = f"CPU élevé: {cpu_percent}% d'utilisation"
            else:
                statut = 'ok'
                message = f"CPU normal: {cpu_percent}% d'utilisation"

            return {
                'statut': statut,
                'message': message,
                'details': resultats
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic CPU: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser le CPU: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_services_windows() -> Dict[str, Any]:
        """Diagnostic des services Windows critiques"""
        if platform.system() != 'Windows':
            return {
                'statut': 'ok',
                'message': 'Diagnostic services non applicable (système non-Windows)',
                'details': {}
            }

        try:
            services_critiques = [
                'Spooler',  # Service d'impression
                'Themes',   # Thèmes
                'AudioSrv', # Audio Windows
                'Dhcp',     # Client DHCP
                'Dnscache', # Client DNS
                'Eventlog', # Journal des événements
            ]

            services_status = {}
            problemes = []

            for service in services_critiques:
                try:
                    result = subprocess.run(
                        ['sc', 'query', service],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if 'RUNNING' in result.stdout:
                        services_status[service] = 'running'
                    elif 'STOPPED' in result.stdout:
                        services_status[service] = 'stopped'
                        problemes.append(f"Service {service} arrêté")
                    else:
                        services_status[service] = 'unknown'
                        problemes.append(f"État du service {service} inconnu")

                except subprocess.TimeoutExpired:
                    services_status[service] = 'timeout'
                    problemes.append(f"Timeout lors de la vérification du service {service}")
                except Exception as e:
                    services_status[service] = f'error {e}'
                    problemes.append(f"Erreur lors de la vérification du service {service}")

            if problemes:
                statut = 'avertissement' if len(problemes) < 3 else 'erreur'
                message = f"{len(problemes)} service(s) avec des problèmes"
            else:
                statut = 'ok'
                message = "Tous les services critiques fonctionnent"

            return {
                'statut': statut,
                'message': message,
                'details': {
                    'services': services_status,
                    'problemes': problemes
                }
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic services: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser les services: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_logiciels() -> Dict[str, Any]:
        """Diagnostic des logiciels installés et processus"""
        try:
            # Processus en cours
            processus = []
            processus_suspects = []

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 10 or info['memory_percent'] > 5:
                        processus.append({
                            'pid': info['pid'],
                            'nom': info['name'],
                            'cpu': info['cpu_percent'],
                            'memoire': info['memory_percent']
                        })

                    # Détecter des processus suspects (optionnel)
                    nom_processus = info['name'].lower()
                    if any(suspect in nom_processus for suspect in ['malware', 'virus', 'trojan']):
                        processus_suspects.append(info['name'])

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Trier par utilisation CPU
            processus.sort(key=lambda x: x['cpu'], reverse=True)
            top_processus = processus[:10]  # Top 10

            resultats = {
                'processus_gourmands': top_processus,
                'nombre_total_processus': len(list(psutil.process_iter())),
                'processus_suspects': processus_suspects
            }

            if processus_suspects:
                statut = 'erreur'
                message = f"Processus suspects détectés: {', '.join(processus_suspects)}"
            elif any(p['cpu'] > 50 for p in top_processus):
                statut = 'avertissement'
                message = "Processus avec forte utilisation CPU détectés"
            else:
                statut = 'ok'
                message = "Processus normaux"

            return {
                'statut': statut,
                'message': message,
                'details': resultats
            }
        except Exception as e:
            logger.error(f"Erreur diagnostic logiciels: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser les logiciels: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_securite() -> Dict[str, Any]:
        """Diagnostic de sécurité du système"""
        try:
            resultats = {}
            problemes_securite = []

            # Vérifier Windows Defender (Windows seulement)
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(
                        ['powershell', '-Command', 'Get-MpComputerStatus'],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )

                    if 'AntivirusEnabled' in result.stdout:
                        if 'True' in result.stdout:
                            resultats['antivirus'] = 'actif'
                        else:
                            resultats['antivirus'] = 'inactif'
                            problemes_securite.append("Antivirus Windows Defender désactivé")
                    else:
                        resultats['antivirus'] = 'inconnu'

                except (subprocess.TimeoutExpired, Exception):
                    resultats['antivirus'] = 'erreur_verification'
            else:
                resultats['antivirus'] = 'non_applicable'

            # Vérifier les mises à jour Windows
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(
                        ['powershell', '-Command', 'Get-WULastResults | Select-Object LastSearchSuccessDate'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.stdout:
                        resultats['derniere_maj'] = result.stdout.strip()
                    else:
                        problemes_securite.append("Impossible de vérifier les mises à jour")

                except (subprocess.TimeoutExpired, Exception):
                    problemes_securite.append("Erreur lors de la vérification des mises à jour")

            # Déterminer le statut global
            if len(problemes_securite) >= 2:
                statut = 'erreur'
                message = f"Problèmes de sécurité détectés: {len(problemes_securite)} problème(s)"
            elif len(problemes_securite) == 1:
                statut = 'avertissement'
                message = f"Problème de sécurité mineur: {problemes_securite[0]}"
            else:
                statut = 'ok'
                message = "Sécurité du système normale"

            return {
                'statut': statut,
                'message': message,
                'details': {
                    'resultats': resultats,
                    'problemes': problemes_securite
                }
            }

        except Exception as e:
            logger.error(f"Erreur diagnostic sécurité: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser la sécurité: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_performance() -> Dict[str, Any]:
        """Diagnostic de performance global"""
        try:
            # Temps de démarrage du système
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600

            # Statistiques de performance
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()

            # Score de performance basé sur plusieurs facteurs
            score_performance = 100

            # Pénalités selon l'utilisation
            if memory.percent > 80:
                score_performance -= 20
            elif memory.percent > 60:
                score_performance -= 10

            # Test rapide de lecture disque
            try:
                disk_test_start = time.time()
                test_file = "test_perf_temp.tmp"
                with open(test_file, 'wb') as f:
                    f.write(b'0' * 1024 * 1024)  # 1MB
                with open(test_file, 'rb') as f:
                    f.read()
                disk_test_time = time.time() - disk_test_start

                import os
                os.remove(test_file)

                if disk_test_time > 2:
                    score_performance -= 15
                elif disk_test_time > 1:
                    score_performance -= 5

            except Exception as e:
                logger.error(f"Erreur diagnostic test: {e}")
                disk_test_time = None

            resultats = {
                'uptime_hours': round(uptime_hours, 1),
                'score_performance': max(0, score_performance),
                'temps_test_disque': disk_test_time,
                'processeurs': cpu_count,
                'memoire_totale_gb': round(memory.total / (1024**3), 2)
            }

            # Déterminer le statut
            if score_performance >= 80:
                statut = 'ok'
                message = f"Performance excellente (score: {score_performance}/100)"
            elif score_performance >= 60:
                statut = 'avertissement'
                message = f"Performance acceptable (score: {score_performance}/100)"
            else:
                statut = 'erreur'
                message = f"Performance dégradée (score: {score_performance}/100)"

            return {
                'statut': statut,
                'message': message,
                'details': resultats
            }

        except Exception as e:
            logger.error(f"Erreur diagnostic performance: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser les performances: {str(e)}",
                'details': {}
            }

    @staticmethod
    def diagnostic_systeme_os() -> Dict[str, Any]:
        """Diagnostic du système d'exploitation"""
        try:
            import platform

            resultats = {
                'systeme': platform.system(),
                'version': platform.version(),
                'release': platform.release(),
                'architecture': platform.architecture()[0],
                'machine': platform.machine(),
                'processeur': platform.processor(),
                'nom_complet': platform.platform()
            }

            # Vérifications spécifiques à Windows
            if platform.system() == 'Windows':
                version_parts = platform.version().split('.')
                if len(version_parts) >= 3:
                    build_number = int(version_parts[2])

                    # Vérifier si c'est une version supportée de Windows
                    if build_number < 19041:  # Windows 10 version 2004
                        statut = 'avertissement'
                        message = "Version de Windows potentiellement obsolète"
                    else:
                        statut = 'ok'
                        message = "Version de Windows à jour"
                else:
                    statut = 'informatif'
                    message = "Informations système collectées"
            else:
                statut = 'informatif'
                message = f"Système {platform.system()} détecté"

            return {
                'statut': statut,
                'message': message,
                'details': resultats
            }

        except Exception as e:
            logger.error(f"Erreur diagnostic système OS: {e}")
            return {
                'statut': 'erreur',
                'message': f"Impossible d'analyser le système: {str(e)}",
                'details': {}
            }

    def sauvegarder_diagnostic(self, type_diagnostic: str, resultat: Dict[str, Any]):
        """Sauvegarde un diagnostic dans la base de données avec durée d'exécution"""
        try:
            duree_execution = time.time() - self.debut_diagnostic

            # Déterminer le niveau d'impact
            niveau_impact = 1
            if resultat['statut'] == 'erreur':
                niveau_impact = 8
            elif resultat['statut'] == 'avertissement':
                niveau_impact = 5
            elif resultat['statut'] == 'informatif':
                niveau_impact = 2

            # Générer des balises automatiques
            balises = [type_diagnostic, resultat['statut']]
            if 'details' in resultat and resultat['details']:
                if 'problemes' in resultat['details']:
                    balises.append('problemes_detectes')
                if 'score_performance' in resultat['details']:
                    balises.append('performance_mesuree')

            DiagnosticSysteme.objects.create(
                session=self.session,
                type_diagnostic=type_diagnostic,
                resultat=resultat['details'],
                statut=resultat['statut'],
                message=resultat['message'],
                duree_execution=duree_execution,
                niveau_impact=niveau_impact,
                balises=balises
            )

        except Exception as e:
            logger.error(f"Erreur sauvegarde diagnostic {type_diagnostic}: {e}")


class ArbreDecisionEngine:
    """Moteur d'arbre de décision pour le questionnaire intelligent"""

    def __init__(self, session: SessionDiagnostic):
        self.session = session
        self.template = self._obtenir_template()

    def _obtenir_template(self) -> Optional[TemplateDiagnostic]:
        """Obtient le template de diagnostic pour la catégorie"""
        try:
            return TemplateDiagnostic.objects.filter(
                categorie=self.session.categorie,
                est_actif=True
            ).first()
        except Exception as e:
            logger.error(f"Erreur obtenier template: {e}")
            return None

    def obtenir_prochaine_question(self) -> Optional[QuestionDiagnostic]:
        """Obtient la prochaine question à poser basée sur les réponses précédentes"""
        # Enregistrer l'action dans l'historique
        HistoriqueDiagnostic.objects.create(
            session=self.session,
            action='reponse',
            utilisateur=self.session.utilisateur,
            details={'action': 'recherche_prochaine_question'}
        )

        # Obtenir toutes les réponses de la session
        reponses_donnees = ReponseDiagnostic.objects.filter(session=self.session)
        questions_repondues = [r.question_id for r in reponses_donnees]

        # Si on a un template, utiliser son ordre
        if self.template:
            template_questions = self.template.template_questions.filter(
                question__actif=True
            ).exclude(
                question__id__in=questions_repondues
            ).order_by('ordre')

            for template_question in template_questions:
                question = template_question.question
                # Utiliser les conditions du template en priorité
                conditions = template_question.condition_affichage or question.condition_affichage

                if self._verifier_conditions_affichage(conditions, reponses_donnees):
                    return question
        else:
            # Fallback vers l'ancienne méthode
            questions_disponibles = QuestionDiagnostic.objects.filter(
                categorie=self.session.categorie,
                actif=True,
                question_parent__isnull=True
            ).exclude(
                id__in=questions_repondues
            ).order_by('ordre')

            for question in questions_disponibles:
                if self._verifier_conditions_affichage(question.condition_affichage, reponses_donnees):
                    return question

        return None

    def _verifier_conditions_affichage(self, conditions: dict, reponses: List[ReponseDiagnostic]) -> bool:
        """Vérifie si les conditions d'affichage sont remplies"""
        if not conditions:
            return True

        # Logique étendue pour les conditions
        if 'question_id' in conditions:
            question_requis_id = conditions['question_id']
            choix_requis = conditions.get('choix_requis', [])

            reponse_requise = next(
                (r for r in reponses if r.question_id == question_requis_id),
                None
            )

            if not reponse_requise:
                return False

            choix_selectionnes = [c.valeur for c in reponse_requise.choix_selectionnes.all()]

            if conditions.get('operateur', 'ET') == 'ET':
                return all(choix in choix_selectionnes for choix in choix_requis)
            else:
                return any(choix in choix_selectionnes for choix in choix_requis)

        # Condition basée sur le score
        if 'score_minimum' in conditions:
            score_actuel = sum(r.score_criticite for r in reponses)
            return score_actuel >= conditions['score_minimum']

        # Condition basée sur les diagnostics système
        if 'diagnostic_requis' in conditions:
            diagnostics = DiagnosticSysteme.objects.filter(session=self.session)
            types_diagnostics = [d.type_diagnostic for d in diagnostics if d.statut == conditions.get('statut_requis', 'erreur')]
            return any(t in types_diagnostics for t in conditions['diagnostic_requis'])

        return True

    def calculer_priorite_estimee(self) -> Tuple[str, int]:
        """Calcule la priorité estimée avec algorithme amélioré"""
        score_total = 0
        nombre_reponses = 0
        poids_questions_critiques = 0

        # Score des réponses du questionnaire avec pondération
        for reponse in ReponseDiagnostic.objects.filter(session=self.session):
            poids = 2 if reponse.question.est_critique else 1
            score_total += reponse.score_criticite * poids
            nombre_reponses += 1

            if reponse.question.est_critique:
                poids_questions_critiques += 1

        # Score des diagnostics système
        diagnostics_erreur = DiagnosticSysteme.objects.filter(
            session=self.session,
            statut='erreur'
        )

        diagnostics_avertissement = DiagnosticSysteme.objects.filter(
            session=self.session,
            statut='avertissement'
        )

        # Calculer l'impact total des diagnostics système
        impact_systeme = sum(d.niveau_impact for d in diagnostics_erreur) + \
                        sum(d.niveau_impact * 0.5 for d in diagnostics_avertissement)

        score_total += impact_systeme

        # Calculer le score de confiance
        score_confiance = 1.0
        if self.session.score_confiance:
            score_confiance = self.session.score_confiance

        # Ajuster le score avec la confiance
        score_final = score_total * score_confiance

        # Déterminer la priorité avec logique améliorée
        if (score_final >= 25 or
            diagnostics_erreur.filter(niveau_impact__gte=8).exists() or
            poids_questions_critiques >= 2):
            return 'critique', int(score_final)
        elif (score_final >= 15 or
              diagnostics_erreur.exists() or
              poids_questions_critiques >= 1):
            return 'urgent', int(score_final)
        elif score_final >= 8 or diagnostics_avertissement.count() >= 2:
            return 'normal', int(score_final)
        else:
            return 'faible', int(score_final)

    def generer_recommandations(self) -> str:
        """Génère des recommandations basées sur les réponses et diagnostics"""
        recommandations = []

        # Analyser les diagnostics système
        diagnostics = DiagnosticSysteme.objects.filter(session=self.session)

        for diagnostic in diagnostics:
            if diagnostic.statut == 'erreur':
                if diagnostic.type_diagnostic == 'memoire':
                    recommandations.append("• Fermez les applications non nécessaires pour libérer de la mémoire")
                    recommandations.append("• Redémarrez votre ordinateur si le problème persiste")
                elif diagnostic.type_diagnostic == 'disque':
                    recommandations.append("• Libérez de l'espace disque en supprimant les fichiers temporaires")
                    recommandations.append("• Videz la corbeille et nettoyez le cache des navigateurs")
                elif diagnostic.type_diagnostic == 'reseau':
                    recommandations.append("• Vérifiez votre connexion Internet")
                    recommandations.append("• Redémarrez votre modem/routeur")
                elif diagnostic.type_diagnostic == 'services':
                    recommandations.append("• Contactez un technicien pour redémarrer les services Windows")

        # Analyser les réponses du questionnaire
        reponses = ReponseDiagnostic.objects.filter(session=self.session)

        for reponse in reponses:
            if reponse.score_criticite >= 8:
                if reponse.question.est_critique:
                    recommandations.append(f"• Problème critique détecté : {reponse.question.titre}")
                    recommandations.append("• Contactez immédiatement le support technique")

        # Appliquer les règles de diagnostic
        regles = RegleDiagnostic.objects.filter(
            categorie=self.session.categorie,
            est_active=True
        )

        for regle in regles:
            if self.evaluer_regle(regle, reponses, diagnostics):
                recommandations.append(f"• {regle.message_utilisateur}")

        if not recommandations:
            recommandations.append("• Aucun problème critique détecté")
            recommandations.append("• Surveillez votre système et contactez le support si nécessaire")

        return "\n".join(recommandations)

    @staticmethod
    def evaluer_regle(regle: RegleDiagnostic, reponses, diagnostics) -> bool:
        """Évalue si une règle de diagnostic doit être appliquée"""
        # Implémentation basique - peut être étendue
        conditions = regle.conditions

        # Exemple de condition:
        # {
        #   "score_minimum": 15,
        #   "diagnostic_erreur": ["memoire", "disque"]
        # }

        if 'score_minimum' in conditions:
            score_total = sum(r.score_criticite for r in reponses)
            if score_total < conditions['score_minimum']:
                return False

        if 'diagnostic_erreur' in conditions:
            types_erreur = [d.type_diagnostic for d in diagnostics if d.statut == 'erreur']
            if not any(t in types_erreur for t in conditions['diagnostic_erreur']):
                return False

        return True
