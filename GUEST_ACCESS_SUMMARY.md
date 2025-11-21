# KEFA Platform - Guest Access Control

## ✅ What GUESTS (Fans) CAN Access (No Login Required)

### Public Pages - Fan View
1. **Homepage** - Platform statistics, featured tournaments
2. **Tournaments List** - View all active and completed tournaments
3. **Tournament Details** - Standings, fixtures, top scorers for any tournament
4. **Leaderboards** - Top teams, top scorers, top players with achievements
5. **Player Profiles** (Public View) - View any player's:
   - Full name, team, bio, profile picture
   - Tournament standings
   - Match history
   - Achievements and badges
   - Trophies won
   - Win rate and statistics
   - ⚠️ This is like viewing Ronaldo's stats on a sports website - PUBLIC INFO
6. **Team Profiles** - View any team's stats, matches, highlights
7. **Highlights Gallery** - Watch verified match highlights
8. **Registration Page** - Sign up for KEFA
9. **Login Page** - Access to login

## ❌ What GUESTS CANNOT Access (Login Required)

### Personal Dashboard & Actions
1. **Player Dashboard** - YOUR personal dashboard showing:
   - Your upcoming matches
   - Your achievements
   - Your tournament registrations
   - Your team stats
   - ⚠️ This is PERSONAL - requires login
2. **Edit Profile** - Modify your player or team information
3. **Tournament Registration** - Register your team for tournaments
4. **Payment Actions** - Pay registration fees, upload payment proofs
5. **Match Actions**:
   - Mark ready for matches
   - Create game codes
   - Join games
   - Upload match highlights
6. **Community Chat** - Participate in chat, create friendly matches
7. **Postponement Requests** - Request to reschedule matches

## 🔐 Admin-Only Access (Staff Members)

1. **Admin Dashboard** - Platform metrics and moderation tools
2. **Payment Verification Queue** - Approve offline payments
3. **Highlight Verification Queue** - Verify and approve match videos
4. **Postponement Approval Queue** - Approve/reject postponement requests

---

## Key Difference: Dashboard vs Profile

### Player Dashboard (Requires Login)
- **URL**: `/dashboard/`
- **Purpose**: YOUR personal control panel
- **Content**: Your matches, your tournaments, your achievements
- **Access**: Only YOU after login

### Player Profile (Public - No Login)
- **URL**: `/players/<player_id>/`
- **Purpose**: Public view of ANY player (like a sports website)
- **Content**: Player's public stats, team, achievements, match history
- **Access**: Anyone (fans, guests, everyone)

**Example**: 
- A fan visiting KEFA can click on any player's name and see their achievements, just like viewing Messi's profile on FIFA.com
- But to access YOUR OWN dashboard and register for tournaments, you must login

---

## Superuser Credentials

**Username**: `admin`  
**Password**: `KEFA@Admin2024`

**Access**: 
- Django Admin Panel: `/admin/`
- Admin Dashboard: `/admin/dashboard/`
- All admin verification queues

**Important**: Change this password in production!

---

**Summary**: Guests have full fan experience (view tournaments, standings, player stats, highlights) but cannot perform actions (register, play, upload, chat). This follows standard sports platform design.
