"""
Production Diagnostic Script for KEFA Template Rendering

This script tests Django template rendering directly to diagnose
production issues where template variables appear as raw syntax.

Run with: python production_diagnostic.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kefa_project.settings')
django.setup()

from django.template import Template, Context
from django.conf import settings
from kefa_project.matches.models import Match
from kefa_project.teams.models import Team
from kefa_project.tournaments.models import Tournament

print("=" * 70)
print("KEFA PRODUCTION TEMPLATE DIAGNOSTIC")
print("=" * 70)
print(f"\nDEBUG Mode: {settings.DEBUG}")
print(f"Template Backend: {settings.TEMPLATES[0]['BACKEND']}")
print(f"Template Dirs: {settings.TEMPLATES[0]['DIRS']}")
print(f"String if Invalid: {settings.TEMPLATES[0]['OPTIONS'].get('string_if_invalid', 'Not Set')}")

# Test 1: Basic Template Rendering
print("\n" + "=" * 70)
print("TEST 1: Basic Template Variable Rendering")
print("=" * 70)

template_str = "Team Name: {{ team.team_name }}"
template = Template(template_str)
team = Team.objects.first()

if team:
    context = Context({'team': team})
    result = template.render(context)
    expected = f"Team Name: {team.team_name}"
    
    print(f"Template: {template_str}")
    print(f"Expected: {expected}")
    print(f"Got:      {result}")
    print(f"[PASS]" if result == expected else "[FAIL]")
else:
    print("[FAIL] No teams in database")

# Test 2: Match Template Rendering
print("\n" + "=" * 70)
print("TEST 2: Match Template Rendering (Production Issue)")
print("=" * 70)

match_template = "{{ match.home_team.team_name }} vs {{ match.away_team.team_name }}"
template = Template(match_template)
match = Match.objects.select_related('home_team', 'away_team').first()

if match:
    context = Context({'match': match})
    result = template.render(context)
    expected = f"{match.home_team.team_name} vs {match.away_team.team_name}"
    
    print(f"Template: {match_template}")
    print(f"Expected: {expected}")
    print(f"Got:      {result}")
    print(f"[PASS]" if result == expected else "[FAIL]")
    
    # Check for raw template syntax in output
    if '{{' in result or '}}' in result:
        print("\n[WARNING] Raw template syntax detected in output!")
        print("   This indicates template rendering is failing.")
else:
    print("[FAIL] No matches in database")

# Test 3: Missing Variable Handling
print("\n" + "=" * 70)
print("TEST 3: Missing Variable Handling")
print("=" * 70)

missing_var_template = "{{ nonexistent_variable }}"
template = Template(missing_var_template)
context = Context({})
result = template.render(context)

print(f"Template: {missing_var_template}")
print(f"Got:      '{result}'")

if settings.DEBUG:
    print("Expected: '' (empty string in DEBUG mode)")
else:
    print("Expected: '***MISSING_VAR:nonexistent_variable***' (production mode)")

# Test 4: Context Processor Test
print("\n" + "=" * 70)
print("TEST 4: Context Processor Availability")
print("=" * 70)

from django.template import RequestContext
from django.test import RequestFactory

factory = RequestFactory()
request = factory.get('/')
request.user = None  # Anonymous user

context = RequestContext(request)
print(f"Available context processors: {len(settings.TEMPLATES[0]['OPTIONS']['context_processors'])}")
for processor in settings.TEMPLATES[0]['OPTIONS']['context_processors']:
    print(f"  - {processor}")

# Test 5: Database Integrity Check
print("\n" + "=" * 70)
print("TEST 5: Database Integrity Check")
print("=" * 70)

teams_with_template_syntax = Team.objects.filter(team_name__contains='{{')
if teams_with_template_syntax.exists():
    print("[FAIL] Found teams with template syntax in names:")
    for team in teams_with_template_syntax:
        print(f"  - ID {team.id}: {team.team_name}")
else:
    print("[PASS] No template syntax found in team names")

tournaments_with_template_syntax = Tournament.objects.filter(name__contains='{{')
if tournaments_with_template_syntax.exists():
    print("[FAIL] Found tournaments with template syntax in names:")
    for tournament in tournaments_with_template_syntax:
        print(f"  - ID {tournament.id}: {tournament.name}")
else:
    print("[PASS] No template syntax found in tournament names")

# Summary
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print("\nIf you see '[FAIL]' above, there's a template rendering issue.")
print("If you see raw {{ }} syntax in output, templates are not being processed.")
print("\nNext steps:")
print("1. Run this script in production environment")
print("2. Check Render logs for template errors")
print("3. Verify WSGI/ASGI configuration")
print("4. Check static file serving configuration")
print("=" * 70)
