from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, date
import random
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.tournaments.models import Tournament, Standing
from kefa_project.matches.models import Match
from kefa_project.highlights.models import Highlight
from kefa_project.achievements.models import Badge, PlayerBadge

class Command(BaseCommand):
    help = 'Seeds the database with 5 years of historical KEFA data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting 5-Year Historical Data Seeding...")
        
        # Team names for diversity
        team_names = [
            "Thunder Strikers", "Shadow Warriors", "Phoenix Rising", "Ice Dragons",
            "Golden Eagles", "Silver Wolves", "Crimson Titans", "Emerald Lions",
            "Royal Knights", "Savage Beasts", "Storm Chasers", "Flame Guardians",
            "Ocean Masters", "Mountain Kings", "Desert Raiders", "Forest Rangers",
            "Galaxy Defenders", "Cosmic Crusaders", "Venom Squad", "Iron Panthers",
            "Blue Dolphins", "Red Scorpions", "Black Hawks", "White Tigers",
            "Night Owls", "Solar Flares", "Lunar Legends", "Star Gazers",
            "Thunder Bolts", "Lightning Strikes", "Tornado Twisters", "Hurricane Force",
            "Avalanche Army", "Earthquake Elite", "Tsunami Tide", "Volcano Vipers"
        ]
        
        # Player names (first + last combinations)
        first_names = ["Mohammed", "Ibrahim", "Usman", "Abubakar", "Yusuf", "Musa", "Hassan", "Ali",
                      "Ahmad", "Abdullahi", "Sani", "Aminu", "Kabir", "Nasiru", "Bashir", "Jamilu"]
        last_names = ["Adamu", "Dan", "Tanko", "Umar", "Bello", "Suleiman", "Garba", "Musa",
                     "Ibrahim", "Aliyu", "Muhammad", "Idris", "Yakubu", "Salisu", "Abubakar", "Ahmad"]
        
        self.stdout.write("Creating users and teams...")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        # User.objects.filter(is_superuser=False).delete()
        # Team.objects.all().delete()
        # Tournament.objects.all().delete()
        # Match.objects.all().delete()
        # Highlight.objects.all().delete()
        
        teams = []
        players_created = []
        
        # Create 36 teams
        for i, team_name in enumerate(team_names[:36], 1):
            username = f"player{i}"
            # Check if user exists
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@kefa.local',
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names)
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
            
            # Create player profile if it doesn't exist
            player, _ = Player.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f"{user.first_name} {user.last_name}",
                    'efootball_id': f"KEF{1000 + i}",
                    'phone_number': f"080{random.randint(10000000, 99999999)}",
                    'device_type': random.choice(['android', 'iphone', 'tablet']),
                    'address': "Birnin Kebbi, Nigeria"
                }
            )
            players_created.append(player)
            
            # Create team if it doesn't exist
            team, _ = Team.objects.get_or_create(
                player=player,
                defaults={
                    'team_name': team_name,
                }
            )
            teams.append(team)
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(teams)} teams"))
        
        # Create tournaments spanning 5 years
        self.stdout.write("Creating tournaments...")
        tournaments_data = []
        
        # 2021 Season
        tournaments_data.extend([
            {"name": "KEFA Spring Championship 2021", "year": 2021, "month": 3, "type": "league"},
            {"name": "Kebbi Summer  Cup 2021", "year": 2021, "month": 6, "type": "knockout"},
            {"name": "KEFA Autumn League 2021", "year": 2021, "month": 9, "type": "league"},
        ])
        
        # 2022 Season
        tournaments_data.extend([
            {"name": "KEFA Premier League 2022", "year": 2022, "month": 2, "type": "league"},
            {"name": "Ramadan Cup 2022", "year": 2022, "month": 4, "type": "knockout"},
            {"name": "KEFA Champions Trophy 2022", "year": 2022, "month": 7, "type": "league"},
            {"name": "Independence Cup 2022", "year": 2022, "month": 10, "type": "knockout"},
        ])
        
        # 2023 Season
        tournaments_data.extend([
            {"name": "KEFA Super League 2023", "year": 2023, "month": 1, "type": "league"},
            {"name": "Grand Masters Cup 2023", "year": 2023, "month": 5, "type": "knockout"},
            {"name": "KEFA Summer Championship 2023", "year": 2023, "month": 8, "type": "league"},
            {"name": "Year-End Showdown 2023", "year": 2023, "month": 12, "type": "knockout"},
        ])
        
        # 2024 Season
        tournaments_data.extend([
            {"name": "KEFA Elite League 2024", "year": 2024, "month": 2, "type": "league"},
            {"name": "Spring Invitational 2024", "year": 2024, "month": 4, "type": "knockout"},
            {"name": "KEFA Champions League 2024", "year": 2024, "month": 7, "type": "league"},
            {"name": "Golden Trophy 2024", "year": 2024, "month": 10, "type": "knockout"},
        ])
        
        # 2025 Season
        tournaments_data.extend([
            {"name": "KEFA Premier Division 2025", "year": 2025, "month": 1, "type": "league"},
            {"name": "Mid-Year Championship 2025", "year": 2025, "month": 6, "type": "knockout"},
            {"name": "KEFA Grand Finals 2025", "year": 2025, "month": 11, "type": "league"},
        ])
        
        # 2026 (Current ongoing)
        tournaments_data.extend([
            {"name": "KEFA Season Opener 2026", "year": 2026, "month": 1, "type": "league"},
        ])
        
        tournaments = []
        for t_data in tournaments_data:
            start_date = date(t_data['year'], t_data['month'], random.randint(1, 20))
            
            # Determine status based on year
            if t_data['year'] < 2026:
                status = 'completed'
            elif t_data['year'] == 2026 and t_data['month'] == 1:
                status = 'ongoing'
            else:
                status = 'locked'
            
            tournament, _ = Tournament.objects.get_or_create(
                name=t_data['name'],
                defaults={
                    'tournament_type': t_data['type'],
                    'team_limit': 16 if t_data['type'] == 'league' else 32,
                    'start_date': start_date,
                    'end_date': start_date + timedelta(days=60 if t_data['type'] == 'league' else 30),
                    'registration_fee': random.choice([0, 500, 1000, 2000]),
                    'prize': f"₦{random.choice([10000, 20000, 50000, 100000])} Prize Pool" if random.random() > 0.3 else "",
                    'status': status,
                    'rules': f"Standard KEFA {t_data['type']} rules apply."
                }
            )
            tournaments.append(tournament)
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(tournaments)} tournaments"))
        
        # Create matches and standings for completed tournaments
        self.stdout.write("Creating matches and standings...")
        match_count = 0
        
        for tournament in tournaments:
            if tournament.status != 'completed':
                continue
            
            # Select random teams for this tournament
            team_count = 16 if tournament.tournament_type == 'league' else 16
            tournament_teams = random.sample(teams, min(team_count, len(teams)))
            
            # Create standings
            for team in tournament_teams:
                played = random.randint(10, 20)
                won = random.randint(3, played)
                drawn = random.randint(0, played - won)
                lost = played - won - drawn
                gf = random.randint(won * 2, won * 4 + 10)
                ga = random.randint(lost, lost * 3 + 5)
                
                Standing.objects.get_or_create(
                    tournament=tournament,
                    team=team,
                    defaults={
                        'played': played,
                        'won': won,
                        'drawn': drawn,
                        'lost': lost,
                        'goals_for': gf,
                        'goals_against': ga,
                        'points': (won * 3) + drawn,
                        'form': ''.join([random.choice(['W', 'D', 'L']) for _ in range(5)])
                    }
                )
            
            # Create matches
            num_matches = random.randint(30, 50) if tournament.tournament_type == 'league' else random.randint(15, 31)
            
            for match_num in range(num_matches):
                home_team, away_team = random.sample(tournament_teams, 2)
                match_date = tournament.start_date + timedelta(days=random.randint(0, 50))
                match_time = timezone.datetime.strptime(f"{random.randint(14, 20)}:00", "%H:%M").time()
                
                home_score = random.randint(0, 5)
                away_score = random.randint(0, 5)
                
                match, created = Match.objects.get_or_create(
                    tournament=tournament,
                    home_team=home_team,
                    away_team=away_team,
                    match_date=match_date,
                    defaults={
                        'match_time': match_time,
                        'status': 'completed',
                        'home_score': home_score,
                        'away_score': away_score,
                        'verified_at': timezone.make_aware(
                            datetime.combine(match_date, match_time) + timedelta(hours=2)
                        )
                    }
                )
                
                if created:
                    match_count += 1
                    
                    # 60% chance of having a highlight
                    if random.random() < 0.6:
                        Highlight.objects.get_or_create(
                            match=match,
                            uploaded_by_team=home_team,
                            defaults={
                                'uploaded_by_side': 'home',
                                'video_url': f"https://youtube.com/watch?v={''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))}",
                                'description': f"Great match! Final score: {home_score}-{away_score}",
                                'status': 'verified',
                                'verified_at': timezone.now()
                            }
                        )
                    
                    # 40% chance of having match summary
                    if random.random() < 0.4:
                        summaries = [
                            f"An intense battle between {home_team.team_name} and {away_team.team_name}. The final score of {home_score}-{away_score} reflects the competitive nature of this {tournament.name} fixture.",
                            f"Thrilling encounter! {home_team.team_name} dominated the first half, while {away_team.team_name} fought back admirably. A memorable match in the {tournament.name}.",
                            f"Classic showdown in {tournament.name}. Both teams displayed excellent skills, with the match ending {home_score}-{away_score}."
                        ]
                        match.match_summary = random.choice(summaries)
                        match.save()
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {match_count} completed matches with highlights"))
        
        # Create some badges
        self.stdout.write("Creating achievement badges...")
        badge_data = [
            {"name": "First Win", "description": "Won your first match", "icon": "🏆"},
            {"name": "10 Matches", "description": "Played 10 matches", "icon": "⚽"},
            {"name": "Tournament Winner", "description": "Won a tournament", "icon": "🥇"},
            {"name": "Top Scorer", "description": "Scored the most goals in a tournament", "icon": "⚡"},
            {"name": "Undefeated Season", "description": "Won a tournament without losing", "icon": "💪"},
        ]
        
        badges_created = 0
        for b_data in badge_data:
            _, created = Badge.objects.get_or_create(
                name=b_data['name'],
                defaults={
                    'description': b_data['description'],
                    'icon': b_data['icon']
                }
            )
            if created:
                badges_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {badges_created} achievement badges"))
        
        self.stdout.write(self.style.SUCCESS("\n*** 5-Year Historical Data Seeding Complete! ***"))
        self.stdout.write(f"   Teams: {len(teams)}")
        self.stdout.write(f"   Tournaments: {len(tournaments)}")
        self.stdout.write(f"   Matches: {match_count}")
        self.stdout.write(f"   Badge Types: {badges_created}")
