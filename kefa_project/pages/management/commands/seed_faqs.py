from django.core.management.base import BaseCommand
from kefa_project.pages.models import FAQ

class Command(BaseCommand):
    help = 'Seeds the database with comprehensive KEFA FAQs'

    def handle(self, *args, **kwargs):
        faqs = [
            {
                "order": 1,
                "question": "What is KEFA?",
                "answer": "KEFA (Kratos eFootball Arena) is the premier digital platform for competitive eFootball mobile gaming in Birnin Kebbi. We organize professional leagues, tournaments, and community events to connect gamers and elevate the esports standards in the region."
            },
            {
                "order": 2,
                "question": "How do I join a tournament?",
                "answer": "To join a tournament, you must first register an account and create your Team Profile. Once set up, navigate to the 'Tournaments' page, select an active tournament with 'Registration Open' status, and click 'Join Now'. Some tournaments may require a registration fee."
            },
            {
                "order": 3,
                "question": "How are payments handled?",
                "answer": "We support both online and offline payments. You can pay securely via Paystack/Flutterwave for instant verification. Alternatively, you can make a bank transfer and select 'Offline Payment' to upload your proof of payment for manual verification by our moderators."
            },
            {
                "order": 4,
                "question": "How is the 'Player of the Week' chosen?",
                "answer": "The Player of the Week is an automated award given to the **Captain** of the best-performing team over the last 7 days. The system ranks teams based on: \n1. Most Wins\n2. Most Goals Scored\n3. Least Goals Conceded\n\nIf you lead your team to dominance, you'll see your face on the Home Page!"
            },
            {
                "order": 5,
                "question": "What happens if my opponent doesn't show up?",
                "answer": "We have a strict **Auto-Loss Logic**. When a match enters the 'Ready Phase', both teams must mark themselves as 'Ready' in their dashboard. If your opponent fails to ready up within the allowed timeframe, the system effectively forfeits the match in your favor."
            },
            {
                "order": 6,
                "question": "How do I upload match highlights?",
                "answer": "After a match is completed, the status changes to 'Awaiting Highlight'. Go to your Dashboard, find the match, and click 'Upload Highlight'. You must upload a screenshot or video proof of the result within 24 hours, or you may face a penalty."
            },
            {
                "order": 7,
                "question": "What are Achievements and Milestones?",
                "answer": "KEFA tracks your career progress automatically. You earn badges for milestones like 'First Win', '10 Matches Played', or 'Tournament Winner'. Check out the **Achievements Gallery** to see all available badges and which ones you've unlocked!"
            },
            {
                "order": 8,
                "question": "Can I reschedule a match?",
                "answer": "Yes. If you cannot play at the scheduled time, go to your dashboard and request a **Postponement**. Your opponent must accept the request, and an Admin must verify the new time. Please request postponements at least 2 hours before kickoff."
            },
            {
                "order": 9,
                "question": "How does Promotion and Relegation work?",
                "answer": "At the end of a League Season, the system automatically identifies the bottom-performing teams for Relegation and the top-performing teams from the Junior League for Promotion. You will receive a system notification if your team is affected."
            },
            {
                "order": 10,
                "question": "How do I play a Friendly Match?",
                "answer": "Visit the Global Chat and look for the **Friendly Match** button. You can generate a Game Code and share it directly in the community chat. Once another player accepts, it tracks as an official friendly match in your history."
            }
        ]

        self.stdout.write("Seeding FAQs...")
        
        # Clear existing to avoid duplicates if re-run
        FAQ.objects.all().delete()
        
        for item in faqs:
            FAQ.objects.create(
                question=item['question'],
                answer=item['answer'],
                order=item['order'],
                is_visible=True
            )
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(faqs)} FAQs.'))
