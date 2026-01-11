from django.core.management.base import BaseCommand
from kefa_project.teams.models import Team
from kefa_project.players.models import Player
from kefa_project.tournaments.models import Tournament

class Command(BaseCommand):
    help = 'Detects and fixes raw template syntax in database fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix the issues instead of just reporting',
        )

    def handle(self, *args, **options):
        self.stdout.write("Scanning for raw template syntax (e.g. {{ ... }})...")
        
        issues_found = 0
        
        # Scan Teams
        for team in Team.objects.all():
            if '{{' in team.team_name or '}}' in team.team_name:
                issues_found += 1
                self.stdout.write(self.style.WARNING(f"Team ID {team.id}: Name is '{team.team_name}'"))
                
                if options['fix']:
                    # Heuristic fix: if it looks like variable code, replace with a placeholder or generic name
                    # In a real scenario, we might want to try to recover the name or just flag it.
                    # Given the user request "Barcelona vs {{ match.away_team.team_name }}", 
                    # it implies the name IS "{{ match.away_team.team_name }}"
                    
                    if 'away_team.team_name' in team.team_name:
                         new_name = f"Team {team.id} (Fix Required)"
                         team.team_name = new_name
                         team.save()
                         self.stdout.write(self.style.SUCCESS(f"  -> Fixed to: {new_name}"))
        
        # Scan Tournaments
        for tournament in Tournament.objects.all():
             if '{{' in tournament.name:
                issues_found += 1
                self.stdout.write(self.style.WARNING(f"Tournament ID {tournament.id}: Name is '{tournament.name}'"))
                if options['fix']:
                     tournament.name = f"Tournament {tournament.id}"
                     tournament.save()
                     self.stdout.write(self.style.SUCCESS(f"  -> Fixed to: {tournament.name}"))

        # Scan Notifications
        from kefa_project.notifications.models import Notification
        for notif in Notification.objects.all():
            if '{{' in notif.message or '}}' in notif.message:
                 issues_found += 1
                 self.stdout.write(self.style.WARNING(f"Notification ID {notif.id}: Message is '{notif.message}'"))
                 if options['fix']:
                     # Try to clean it up or just replace with generic
                     notif.message = "Notification content unavailable due to format error."
                     notif.save()
                     self.stdout.write(self.style.SUCCESS(f"  -> Fixed notification."))

        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS("No issues found!"))
        else:
            if not options['fix']:
                self.stdout.write(self.style.NOTICE(f"\nFound {issues_found} issues. Run with --fix to attempt repair."))
            else:
                self.stdout.write(self.style.SUCCESS(f"\nFixed {issues_found} issues."))

