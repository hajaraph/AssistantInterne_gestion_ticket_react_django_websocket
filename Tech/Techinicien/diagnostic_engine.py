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
        """Diagnostic de performance global avec détection des applications gourmandes"""
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
            disk_test_time = None
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
                logger.error(f"Erreur diagnostic test disque: {e}")
                disk_test_time = None

            # Détecter les applications gourmandes (processus avec forte utilisation)
            applications_gourmandes = []
            processus_total = 0

            try:
                # Attendre un moment pour avoir des mesures précises du CPU
                time.sleep(1)

                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                    try:
                        info = proc.info
                        processus_total += 1

                        # Critères pour une application gourmande
                        cpu_seuil = 15.0  # Plus de 15% CPU
                        mem_seuil = 5.0   # Plus de 5% RAM

                        if (info['cpu_percent'] and info['cpu_percent'] > cpu_seuil) or \
                           (info['memory_percent'] and info['memory_percent'] > mem_seuil):

                            # Calculer la mémoire en MB
                            memory_mb = 0
                            if info['memory_info']:
                                memory_mb = round(info['memory_info'].rss / (1024 * 1024), 1)

                            app_info = {
                                'nom': info['name'],
                                'pid': info['pid'],
                                'cpu_percent': round(info['cpu_percent'] or 0, 1),
                                'memory_percent': round(info['memory_percent'] or 0, 1),
                                'memory_mb': memory_mb,
                                'impact_performance': 'elevé' if (info['cpu_percent'] or 0) > 25 or (info['memory_percent'] or 0) > 10 else 'moyen'
                            }

                            # Éviter les doublons (même nom de processus)
                            if not any(app['nom'] == app_info['nom'] for app in applications_gourmandes):
                                applications_gourmandes.append(app_info)

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Trier par impact (CPU + mémoire)
                applications_gourmandes.sort(
                    key=lambda x: (x['cpu_percent'] + x['memory_percent']),
                    reverse=True
                )

                # Garder seulement les 10 plus gourmandes
                applications_gourmandes = applications_gourmandes[:10]

                # Ajuster le score de performance selon les applications détectées
                if applications_gourmandes:
                    apps_critiques = [app for app in applications_gourmandes if app['impact_performance'] == 'elevé']
                    if len(apps_critiques) >= 3:
                        score_performance -= 20
                    elif len(apps_critiques) >= 1:
                        score_performance -= 10
                    elif len(applications_gourmandes) >= 5:
                        score_performance -= 5

            except Exception as e:
                logger.error(f"Erreur lors de la détection des applications gourmandes: {e}")

            resultats = {
                'uptime_hours': round(uptime_hours, 1),
                'score_performance': max(0, score_performance),
                'temps_test_disque': disk_test_time,
                'processeurs': cpu_count,
                'memoire_totale_gb': round(memory.total / (1024**3), 2),
                'applications_gourmandes': applications_gourmandes,
                'nombre_processus_total': processus_total,
                'utilisation_cpu_actuelle': psutil.cpu_percent(interval=0.1),
                'utilisation_memoire_actuelle': memory.percent
            }

            # Déterminer le statut avec prise en compte des applications gourmandes
            if score_performance >= 80:
                statut = 'ok'
                message = f"Performance excellente (score: {score_performance}/100)"
            elif score_performance >= 60:
                statut = 'avertissement'
                message = f"Performance acceptable (score: {score_performance}/100)"
                if applications_gourmandes:
                    message += f" - {len(applications_gourmandes)} application(s) gourmande(s) détectée(s)"
            else:
                statut = 'erreur'
                message = f"Performance dégradée (score: {score_performance}/100)"
                if applications_gourmandes:
                    apps_critiques = [app for app in applications_gourmandes if app['impact_performance'] == 'elevé']
                    if apps_critiques:
                        message += f" - {len(apps_critiques)} application(s) très gourmande(s)"

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
        """Génère des recommandations personnalisées basées sur les réponses et diagnostics"""
        recommandations = []
        problemes_detectes = []

        # Analyser les diagnostics système avec recommandations spécifiques
        diagnostics = DiagnosticSysteme.objects.filter(session=self.session)

        for diagnostic in diagnostics:
            if diagnostic.statut == 'erreur':
                if diagnostic.type_diagnostic == 'memoire':
                    utilisation = diagnostic.resultat.get('utilisation_pourcentage', 0)
                    if utilisation > 90:
                        recommandations.append(f"• Mémoire critique ({utilisation}% utilisée)")
                        recommandations.append("  → Fermez immédiatement les applications non nécessaires")
                        recommandations.append("  → Redémarrez votre ordinateur pour libérer la mémoire")
                        problemes_detectes.append("memoire_critique")
                    elif utilisation > 80:
                        recommandations.append(f"• Mémoire élevée ({utilisation}% utilisée)")
                        recommandations.append("  → Fermez les applications gourmandes en mémoire")

                elif diagnostic.type_diagnostic == 'disque':
                    disques_pleins = []
                    for disque in diagnostic.resultat.get('disques', []):
                        if disque.get('pourcentage', 0) > 90:
                            disques_pleins.append(f"{disque.get('mountpoint', 'N/A')} ({disque.get('pourcentage', 0)}%)")

                    if disques_pleins:
                        recommandations.append(f"• Disque(s) presque plein(s): {', '.join(disques_pleins)}")
                        recommandations.append("  → Supprimez les fichiers temporaires et la corbeille")
                        recommandations.append("  → Désinstallez les programmes inutiles")
                        recommandations.append("  → Déplacez vos fichiers vers un disque externe")
                        problemes_detectes.append("disque_plein")

                elif diagnostic.type_diagnostic == 'reseau':
                    if not diagnostic.resultat.get('internet', True):
                        recommandations.append("• Pas de connexion Internet détectée")
                        recommandations.append("  → Vérifiez que votre câble Ethernet est branché")
                        recommandations.append("  → Redémarrez votre modem/routeur (débranchez 30 secondes)")
                        recommandations.append("  → Contactez votre fournisseur Internet si le problème persiste")
                        problemes_detectes.append("reseau_indisponible")
                    else:
                        recommandations.append("• Problème de connectivité réseau")
                        recommandations.append("  → Testez votre connexion avec un autre appareil")
                        recommandations.append("  → Redémarrez votre ordinateur")

                elif diagnostic.type_diagnostic == 'cpu':
                    utilisation = diagnostic.resultat.get('utilisation_pourcentage', 0)
                    if utilisation > 90:
                        recommandations.append(f"• Processeur surchargé ({utilisation}% d'utilisation)")
                        recommandations.append("  → Ouvrez le Gestionnaire des tâches (Ctrl+Shift+Échap)")
                        recommandations.append("  → Arrêtez les processus qui consomment le plus")
                        recommandations.append("  → Redémarrez si nécessaire")
                        problemes_detectes.append("cpu_surcharge")

                elif diagnostic.type_diagnostic == 'services':
                    services_arretes = diagnostic.resultat.get('problemes', [])
                    if services_arretes:
                        recommandations.append("• Services Windows critiques arrêtés")
                        for probleme in services_arretes[:3]:  # Limiter à 3 pour ne pas surcharger
                            recommandations.append(f"  → {probleme}")
                        recommandations.append("  → Contactez le support technique pour redémarrer ces services")
                        problemes_detectes.append("services_arretes")

                elif diagnostic.type_diagnostic == 'logiciels':
                    processus_gourmands = diagnostic.resultat.get('processus_gourmands', [])
                    if processus_gourmands:
                        top_processus = processus_gourmands[0]  # Le plus gourmand
                        if top_processus.get('cpu', 0) > 50:
                            nom_processus = top_processus.get('nom', 'Processus inconnu')
                            cpu_usage = top_processus.get('cpu', 0)
                            recommandations.append(f"• Le logiciel '{nom_processus}' consomme beaucoup de ressources ({cpu_usage}% CPU)")

                            # Recommandations spécifiques selon le processus
                            if 'chrome' in nom_processus.lower() or 'firefox' in nom_processus.lower():
                                recommandations.append("  → Fermez les onglets inutiles de votre navigateur")
                                recommandations.append("  → Redémarrez votre navigateur")
                            elif 'office' in nom_processus.lower() or 'word' in nom_processus.lower() or 'excel' in nom_processus.lower():
                                recommandations.append("  → Fermez les documents Office non utilisés")
                                recommandations.append("  → Redémarrez l'application Office")
                            else:
                                recommandations.append(f"  → Fermez '{nom_processus}' si vous n'en avez pas besoin")
                                recommandations.append("  → Redémarrez l'application si nécessaire")
                            problemes_detectes.append("logiciel_gourmand")

                        # Détecter spécifiquement les applications qui utilisent plus de 15% de RAM
                        applications_ram_elevees = [
                            app for app in processus_gourmands
                            if app.get('memory_percent', 0) > 15
                        ]

                        if applications_ram_elevees:
                            recommandations.append("• Applications consommant beaucoup de mémoire RAM détectées :")
                            for app in applications_ram_elevees[:5]:  # Top 5 des plus gourmandes en RAM
                                nom = app.get('nom', 'Processus inconnu')
                                mem_percent = app.get('memory_percent', 0)
                                mem_mb = app.get('memory_mb', 0)

                                recommandations.append(f"  🔴 {nom} utilise {mem_percent:.1f}% de RAM ({mem_mb} MB)")

                                # Recommandations spécifiques selon l'application
                                nom_lower = nom.lower()
                                if 'chrome' in nom_lower or 'firefox' in nom_lower or 'edge' in nom_lower:
                                    recommandations.append("     → Fermez les onglets inutiles du navigateur")
                                    recommandations.append("     → Utilisez moins d'extensions")
                                elif 'office' in nom_lower or 'word' in nom_lower or 'excel' in nom_lower:
                                    recommandations.append("     → Fermez les documents Office volumineux")
                                    recommandations.append("     → Redémarrez l'application Office")
                                elif 'photoshop' in nom_lower or 'illustrator' in nom_lower or 'premiere' in nom_lower:
                                    recommandations.append("     → Fermez Adobe si vous ne l'utilisez pas")
                                    recommandations.append("     → Réduisez la taille de l'historique d'annulation")
                                elif 'teams' in nom_lower:
                                    recommandations.append("     → Quittez Microsoft Teams si non nécessaire")
                                    recommandations.append("     → Désactivez le démarrage automatique")
                                elif 'spotify' in nom_lower or 'discord' in nom_lower:
                                    recommandations.append("     → Fermez l'application si elle n'est pas utilisée")
                                elif 'steam' in nom_lower or 'epic' in nom_lower:
                                    recommandations.append("     → Fermez le launcher de jeux si inutilisé")
                                else:
                                    recommandations.append(f"     → Fermez '{nom}' pour libérer de la mémoire")
                                    recommandations.append("     → Redémarrez l'application si nécessaire")

                            recommandations.append("")
                            recommandations.append("  ATTENTION: Ces applications consomment beaucoup de mémoire RAM")
                            recommandations.append("  → Votre ordinateur peut être ralenti par ces logiciels")
                            recommandations.append("  → Fermez ceux que vous n'utilisez pas actuellement")
                            recommandations.append("  → Redémarrez votre PC si nécessaire pour libérer la mémoire")
                            problemes_detectes.append("applications_ram_elevees")

                    processus_suspects = diagnostic.resultat.get('processus_suspects', [])
                    if processus_suspects:
                        recommandations.append("• Processus suspects détectés")
                        recommandations.append("  → Lancez immédiatement un scan antivirus complet")
                        recommandations.append("  → Contactez le support informatique URGENT")
                        problemes_detectes.append("processus_suspect")

                elif diagnostic.type_diagnostic == 'securite':
                    problemes_securite = diagnostic.resultat.get('problemes', [])
                    for probleme in problemes_securite:
                        if 'antivirus' in probleme.lower():
                            recommandations.append("• Antivirus désactivé ou non fonctionnel")
                            recommandations.append("  → Activez Windows Defender ou votre antivirus")
                            recommandations.append("  → Lancez une analyse complète du système")
                        elif 'mise' in probleme.lower():
                            recommandations.append("• Mises à jour système manquantes")
                            recommandations.append("  → Allez dans Paramètres > Windows Update")
                            recommandations.append("  → Installez toutes les mises à jour disponibles")
                    problemes_detectes.append("securite_compromise")

                elif diagnostic.type_diagnostic == 'performance':
                    score = diagnostic.resultat.get('score_performance', 100)
                    if score < 60:
                        recommandations.append(f"• Performances dégradées (Score: {score}/100)")

                        # Analyser les causes spécifiques
                        temps_disque = diagnostic.resultat.get('temps_test_disque')
                        if temps_disque and temps_disque > 2:
                            recommandations.append("  → Votre disque dur est lent, envisagez un SSD")
                            recommandations.append("  → Défragmentez votre disque dur")

                        uptime = diagnostic.resultat.get('uptime_hours', 0)
                        if uptime > 168:  # Plus d'une semaine
                            recommandations.append(f"  → Votre PC fonctionne depuis {int(uptime)}h, redémarrez-le")

                        # Afficher les applications gourmandes détectées
                        applications_gourmandes = diagnostic.resultat.get('applications_gourmandes', [])
                        if applications_gourmandes:
                            recommandations.append("")
                            recommandations.append("Applications consommant le plus de ressources :")

                            for i, app in enumerate(applications_gourmandes[:5], 1):  # Top 5 seulement
                                nom = app.get('nom', 'Processus inconnu')
                                cpu = app.get('cpu_percent', 0)
                                mem = app.get('memory_percent', 0)
                                mem_mb = app.get('memory_mb', 0)
                                impact = app.get('impact_performance', 'moyen')

                                # Indicateur selon l'impact ET spécial pour RAM élevée
                                if mem > 15:
                                    indicateur = "(RAM ÉLEVÉE)"
                                elif impact == 'elevé':
                                    indicateur = "(ÉLEVÉ)"
                                else:
                                    indicateur = "(MOYEN)"

                                recommandations.append(f"  {indicateur} {i}. {nom}")
                                recommandations.append(f"     CPU: {cpu}% | RAM: {mem}% ({mem_mb} MB)")

                                # Conseils spécifiques selon l'application avec focus sur la RAM
                                nom_lower = nom.lower()
                                if mem > 15:  # Priorité aux recommandations RAM
                                    if 'chrome' in nom_lower or 'firefox' in nom_lower or 'edge' in nom_lower:
                                        recommandations.append("     → Votre navigateur utilise trop de RAM, fermez les onglets")
                                    elif 'office' in nom_lower or 'word' in nom_lower or 'excel' in nom_lower or 'powerpoint' in nom_lower:
                                        recommandations.append("     → Office consomme trop de mémoire, redémarrez l'application")
                                    elif 'teams' in nom_lower:
                                        recommandations.append("     → Teams utilise trop de RAM, quittez si non nécessaire")
                                    elif 'photoshop' in nom_lower or 'illustrator' in nom_lower:
                                        recommandations.append("     → Adobe consomme beaucoup de RAM, fermez si inutilisé")
                                    else:
                                        recommandations.append(f"     → '{nom}' utilise trop de mémoire, fermez-le")
                                elif 'chrome' in nom_lower or 'firefox' in nom_lower or 'edge' in nom_lower:
                                    recommandations.append("     → Fermez les onglets inutiles du navigateur")
                                elif 'office' in nom_lower or 'word' in nom_lower or 'excel' in nom_lower or 'powerpoint' in nom_lower:
                                    recommandations.append("     → Fermez les documents Office non utilisés")
                                    recommandations.append("     → Redémarrez l'application Office")
                                elif 'teams' in nom_lower:
                                    recommandations.append("     → Quittez Microsoft Teams si non nécessaire")
                                elif 'outlook' in nom_lower:
                                    recommandations.append("     → Redémarrez Outlook ou réduisez les emails en cache")
                                elif 'photoshop' in nom_lower or 'illustrator' in nom_lower:
                                    recommandations.append("     → Fermez Adobe si vous ne l'utilisez pas")
                                elif 'zoom' in nom_lower or 'skype' in nom_lower:
                                    recommandations.append("     → Fermez l'application de visioconférence")
                                elif 'spotify' in nom_lower or 'vlc' in nom_lower:
                                    recommandations.append("     → Pausez ou fermez l'application multimédia")
                                elif impact == 'elevé':
                                    recommandations.append(f"     → Fermez '{nom}' si vous ne l'utilisez pas")
                                    recommandations.append("     → Redémarrez l'application si nécessaire")

                            recommandations.append("")
                            apps_critiques = [app for app in applications_gourmandes if app.get('impact_performance') == 'elevé']
                            apps_ram_elevees = [app for app in applications_gourmandes if app.get('memory_percent', 0) > 15]

                            if apps_ram_elevees:
                                recommandations.append(f"🔴 ALERTE MÉMOIRE: {len(apps_ram_elevees)} application(s) utilisent plus de 15% de RAM")
                                recommandations.append("  → Votre système est ralenti par une consommation excessive de mémoire")
                                recommandations.append("  → Fermez ces applications ou redémarrez votre PC immédiatement")
                            elif apps_critiques:
                                recommandations.append(f"ATTENTION: {len(apps_critiques)} application(s) ont un impact élevé sur les performances")
                                recommandations.append("  → Votre système est lent car ces logiciels consomment beaucoup")
                                recommandations.append("  → Veuillez les arrêter ou redémarrer votre PC si nécessaire")

                        recommandations.append("  → Nettoyez les fichiers temporaires")
                        recommandations.append("  → Désactivez les programmes au démarrage inutiles")
                        problemes_detectes.append("performance_degradee")

                    # Même si les performances sont acceptables, montrer les apps gourmandes en RAM
                    elif diagnostic.statut == 'avertissement':
                        applications_gourmandes = diagnostic.resultat.get('applications_gourmandes', [])
                        if applications_gourmandes:
                            apps_ram_elevees = [app for app in applications_gourmandes if app.get('memory_percent', 0) > 15]

                            if apps_ram_elevees:
                                recommandations.append("")
                                recommandations.append("Applications utilisant beaucoup de mémoire RAM détectées :")
                                for app in apps_ram_elevees[:3]:  # Top 3 des plus gourmandes en RAM
                                    nom = app.get('nom', 'Processus inconnu')
                                    mem = app.get('memory_percent', 0)
                                    mem_mb = app.get('memory_mb', 0)
                                    recommandations.append(f"  🔴 {nom} (RAM: {mem:.1f}% - {mem_mb} MB)")

                                    # Conseil spécifique
                                    nom_lower = nom.lower()
                                    if 'chrome' in nom_lower or 'firefox' in nom_lower:
                                        recommandations.append("     → Votre navigateur utilise trop de RAM, fermez les onglets inutiles")
                                    elif 'office' in nom_lower:
                                        recommandations.append("     → Office consomme beaucoup de mémoire, redémarrez l'application")
                                    else:
                                        recommandations.append(f"     → '{nom}' utilise trop de mémoire, veuillez l'arrêter")

                                recommandations.append("  → Ces applications ralentissent votre ordinateur")
                                recommandations.append("  → Fermez-les ou redémarrez votre PC pour libérer la mémoire")
                            else:
                                apps_critiques = [app for app in applications_gourmandes if app.get('impact_performance') == 'elevé']
                                if apps_critiques:
                                    recommandations.append("")
                                    recommandations.append("Applications gourmandes détectées :")
                                    for app in apps_critiques[:3]:  # Top 3 des plus critiques
                                        nom = app.get('nom', 'Processus inconnu')
                                        cpu = app.get('cpu_percent', 0)
                                        mem = app.get('memory_percent', 0)
                                        recommandations.append(f"  (ELEVÉ) {nom} (CPU: {cpu}%, RAM: {mem}%)")

                                        # Conseil spécifique
                                        nom_lower = nom.lower()
                                        if 'chrome' in nom_lower or 'firefox' in nom_lower:
                                            recommandations.append("     → Votre navigateur est lent, fermez les onglets inutiles")
                                        elif 'office' in nom_lower:
                                            recommandations.append("     → Office consomme beaucoup, redémarrez l'application")
                                        else:
                                            recommandations.append(f"     → Votre système est ralenti par '{nom}', veuillez l'arrêter")

                                    recommandations.append("  → Si vous ne pouvez pas arrêter ces applications, redémarrez votre PC")

            elif diagnostic.statut == 'avertissement':
                # Recommandations pour les avertissements (moins urgentes)
                if diagnostic.type_diagnostic == 'memoire':
                    utilisation = diagnostic.resultat.get('utilisation_pourcentage', 0)
                    recommandations.append(f"• Utilisation mémoire élevée ({utilisation}%)")
                    recommandations.append("  → Surveillez votre utilisation de mémoire")
                elif diagnostic.type_diagnostic == 'disque':
                    recommandations.append("• Espace disque limité")
                    recommandations.append("  → Prévoyez un nettoyage de vos fichiers")

        # Analyser les réponses du questionnaire pour des recommandations spécifiques
        reponses = ReponseDiagnostic.objects.filter(session=self.session)

        for reponse in reponses:
            if reponse.score_criticite >= 8:
                question_titre = reponse.question.titre.lower()

                # Recommandations basées sur les questions critiques
                if 'allume' in question_titre or 'démarre' in question_titre:
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]
                    if 'non' in choix_selectionnes:
                        recommandations.append("• Ordinateur ne démarre pas")
                        recommandations.append("  → Vérifiez que l'alimentation est branchée")
                        recommandations.append("  → Appuyez fermement sur le bouton power")
                        recommandations.append("  → Contactez le support technique si rien ne se passe")
                    elif 'intermittent' in choix_selectionnes:
                        recommandations.append("• Démarrage intermittent")
                        recommandations.append("  → Problème d'alimentation possible")
                        recommandations.append("  → Contactez le support technique rapidement")

                elif 'bruit' in question_titre:
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]
                    if 'disque_bruit' in choix_selectionnes:
                        recommandations.append("• Bruits suspects du disque dur")
                        recommandations.append("  → SAUVEGARDEZ VOS DONNÉES IMMÉDIATEMENT")
                        recommandations.append("  → Contactez le support technique URGENT")
                        recommandations.append("  → Ne forcez pas l'arrêt de l'ordinateur")

                elif 'écran' in question_titre or 'affichage' in question_titre:
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]
                    if 'noir' in choix_selectionnes:
                        recommandations.append("• Écran noir")
                        recommandations.append("  → Vérifiez le câble d'alimentation de l'écran")
                        recommandations.append("  → Vérifiez le câble vidéo (HDMI/VGA)")
                        recommandations.append("  → Testez avec un autre écran si possible")

                elif 'internet' in question_titre or 'wifi' in question_titre:
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]
                    if 'non' in choix_selectionnes or 'aucun' in choix_selectionnes:
                        if 'internet' not in problemes_detectes:  # Éviter les doublons
                            recommandations.append("• Pas d'accès Internet")
                            recommandations.append("  → Vérifiez l'icône Wi-Fi dans la barre des tâches")
                            recommandations.append("  → Reconnectez-vous au Wi-Fi de l'entreprise")

                elif 'email' in question_titre or 'messagerie' in question_titre:
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]
                    if 'impossible' in choix_selectionnes or 'aucun' in choix_selectionnes:
                        recommandations.append("• Problème de messagerie")
                        recommandations.append("  → Redémarrez Outlook ou votre client email")
                        recommandations.append("  → Vérifiez vos paramètres de compte")
                        recommandations.append("  → Contactez le support si le problème persiste")

                elif 'logiciel' in question_titre or 'application' in question_titre:
                    # Analyser la réponse textuelle pour identifier le logiciel
                    texte_reponse = reponse.reponse_texte or ''
                    choix_selectionnes = [c.valeur for c in reponse.choix_selectionnes.all()]

                    if 'office' in choix_selectionnes:
                        recommandations.append("• Problème avec Microsoft Office")
                        recommandations.append("  → Redémarrez l'application Office concernée")
                        recommandations.append("  → Réparez l'installation Office via Panneau de configuration")
                    elif 'navigateur' in choix_selectionnes:
                        recommandations.append("• Problème de navigateur web")
                        recommandations.append("  → Videz le cache et les cookies")
                        recommandations.append("  → Désactivez temporairement les extensions")
                        recommandations.append("  → Redémarrez le navigateur")
                    elif 'windows' in choix_selectionnes:
                        recommandations.append("• Problème système Windows")
                        recommandations.append("  → Redémarrez l'ordinateur")
                        recommandations.append("  → Vérifiez les mises à jour Windows")
                        recommandations.append("  → Contactez le support technique")

        # Appliquer les règles de diagnostic avec messages personnalisés
        regles = RegleDiagnostic.objects.filter(
            categorie=self.session.categorie,
            est_active=True
        )

        for regle in regles:
            try:
                if self._evaluer_regle(regle, reponses, diagnostics):
                    # Ajouter les recommandations de la règle
                    message_regle = regle.description or f"Règle appliquée: {regle.nom}"
                    recommandations.append(f"• {message_regle}")
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation de la règle {regle.nom}: {e}")
                continue

        # Recommandations générales si pas de problèmes critiques
        if not any(p in problemes_detectes for p in ['memoire_critique', 'cpu_surcharge', 'disque_plein', 'processus_suspect']):
            # Calculer le score global
            score_total = sum(r.score_criticite for r in reponses)

            if score_total < 5:
                recommandations.insert(0, "Votre système semble fonctionner correctement")
                recommandations.append("• Conseils préventifs :")
                recommandations.append("  → Redémarrez votre PC au moins une fois par semaine")
                recommandations.append("  → Maintenez vos logiciels à jour")
                recommandations.append("  → Sauvegardez régulièrement vos documents importants")
            elif score_total < 15:
                recommandations.insert(0, "Quelques problèmes mineurs détectés")
                recommandations.append("• Actions recommandées :")
                recommandations.append("  → Surveillez les performances de votre système")
                recommandations.append("  → Appliquez les recommandations ci-dessus")
            else:
                recommandations.insert(0, "Plusieurs problèmes nécessitent votre attention")

        # Ajouter des recommandations de contact selon la gravité
        if any(p in problemes_detectes for p in ['processus_suspect', 'disque_bruit']):
            recommandations.append("")
            recommandations.append("CONTACT URGENT RECOMMANDÉ")
            recommandations.append("Appelez le support technique immédiatement")
        elif any(p in problemes_detectes for p in ['memoire_critique', 'cpu_surcharge', 'services_arretes']):
            recommandations.append("")
            recommandations.append("Contact support technique recommandé dans les 24h")
        elif len(problemes_detectes) > 0:
            recommandations.append("")
            recommandations.append("N'hésitez pas à contacter le support si vous avez des questions")

        # S'assurer qu'il y a toujours des recommandations
        if not recommandations:
            recommandations.append("✅ Aucun problème critique détecté")
            recommandations.append("• Votre système fonctionne normalement")
            recommandations.append("• Continuez à surveiller les performances")
            recommandations.append("• Contactez le support si vous rencontrez des difficultés")

        # Retourner une chaîne non vide
        result = "\n".join(recommandations)
        return result if result else "Diagnostic complété. Aucune recommandation spécifique nécessaire."

    def _evaluer_regle(self, regle: RegleDiagnostic, reponses: List[ReponseDiagnostic],
                      diagnostics: List[DiagnosticSysteme]) -> bool:
        """Évalue si une règle de diagnostic doit être appliquée"""
        try:
            conditions = regle.conditions or {}

            # Exemple de logique d'évaluation basique
            if 'score_minimum' in conditions:
                score_total = sum(r.score_criticite for r in reponses)
                return score_total >= conditions['score_minimum']

            if 'diagnostic_statut' in conditions:
                statuts_requis = conditions['diagnostic_statut']
                diagnostics_avec_statut = [d for d in diagnostics if d.statut in statuts_requis]
                return len(diagnostics_avec_statut) > 0

            # Si aucune condition spécifique, appliquer la règle
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la règle {regle.nom}: {e}")
            return False

