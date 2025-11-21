# KEFA - Kebbi eFootball Arena

## Overview

KEFA is a digital esports platform designed for eFootball mobile gamers in Birnin Kebbi, Nigeria. The platform manages tournaments, matches, teams, and players with a focus on real-time match coordination, payment processing, highlight verification, and community engagement. Built with Django, it provides a complete ecosystem for organizing and running competitive mobile gaming tournaments with automated fixture generation, standings management, and achievement tracking.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Django 5.2.8**: Main web framework handling all business logic, models, and views
- **Django Channels (Daphne)**: Enables WebSocket support for real-time chat functionality
- **Celery**: Asynchronous task queue for scheduled jobs including match window checks and deadline monitoring
- **Django REST Framework**: Provides API capabilities (installed but API endpoints not fully implemented in visible code)

### Database Layer
- **ORM**: Django's built-in ORM for database operations
- **Database**: Not explicitly specified in settings, defaults to SQLite for development
- **Model Structure**:
  - Players: User profiles with eFootball IDs and device information
  - Teams: One-to-one relationship with players, includes squad images
  - Tournaments: Supports multiple formats (league, knockout, group stage, Champions League)
  - Matches: Complex state machine with 12+ status transitions
  - Standings: Calculated tournament rankings
  - Payments: Multi-gateway support with offline verification
  - Achievements: Badges and trophies with automatic awarding
  - Highlights: Video verification system with admin approval

### Real-time Communication
- **WebSockets (Django Channels)**: Community chat room implementation
- **ASGI**: Configured to handle both HTTP and WebSocket protocols
- **Channel Layers**: Group-based messaging for community chat

### Task Scheduling
- **Celery Beat**: Periodic task execution
- **Scheduled Tasks**:
  - `check_match_ready_windows`: Runs every 60 seconds to monitor match readiness and enforce 5-minute windows
  - `check_highlight_deadlines`: Runs every hour to track 24-hour highlight upload deadlines
- **Problem Solved**: Automatic forfeit enforcement and deadline management without manual admin intervention

### File Storage
- **Cloudinary**: Cloud-based media storage for images and videos
- **Upload Categories**:
  - Player profile pictures
  - Team logos and squad images
  - Payment proofs
  - Match highlights
  - Badge icons
  - Highlight thumbnails

### Authentication & Authorization
- **Django Auth**: Built-in authentication system
- **User Model**: Extended with one-to-one Player profile
- **Permissions**: Staff-only views for payment and highlight verification using `@staff_member_required` decorator
- **Registration Flow**: Atomic transaction creating User → Player → Team in single operation

### State Management Pattern
- **Match State Machine**: Complex workflow with validation at each transition
  - `scheduled` → `ready_pending` (5-minute window)
  - `ready_pending` → `creating_game` (both teams ready)
  - `creating_game` → `waiting_join` (home team creates code)
  - `waiting_join` → `in_progress` (away team joins)
  - `in_progress` → `awaiting_highlight` (match finished)
  - `awaiting_highlight` → `pending_verification` (highlight uploaded)
  - `pending_verification` → `completed` (admin verifies)
  - Forfeit states for timeout violations
- **Rationale**: Prevents cheating and ensures both teams follow proper match flow

### Tournament Management
- **Fixture Generation**: Automatic fixture creation upon tournament capacity
- **Formats Supported**:
  - Round-robin leagues
  - Single-elimination knockout
  - Group stages
  - Mixed formats
- **Promotion/Relegation**: Multi-tier league system with automatic promotion
- **Signal-Based Automation**: `post_save` signal on TournamentRegistration triggers fixture generation when full

### Payment Processing
- **Multi-Gateway Support**:
  - Paystack (instant online payments)
  - Flutterwave (alternative online gateway)
  - Offline bank transfer with proof upload
- **Verification Workflow**: Admin queue for manual verification of offline payments
- **Transaction Tracking**: Unique reference IDs for all payments
- **Webhook Integration**: Paystack webhook endpoint for payment confirmations

### Progressive Web App (PWA)
- **Service Worker**: Basic offline caching strategy
- **Manifest**: Configured for mobile installation
- **Theme**: Gold (#FFD700) primary color matching brand
- **Target**: Mobile-first design for smartphone users

### Admin Verification Queues
- **Payment Queue**: Staff interface for verifying bank transfer proofs
- **Highlight Queue**: Admin review of match videos with score entry
- **Design Pattern**: Separation of user submission from admin approval ensures data integrity

### Achievement System
- **Automatic Awards**: Tournament completion triggers badge/trophy distribution
- **Badge Types**: Winner, runner-up, top scorer, best defense, custom
- **Service Layer**: `award_automatic_achievements()` encapsulates awarding logic
- **Rationale**: Gamification increases player engagement and retention

## External Dependencies

### Third-Party Services
- **Cloudinary**: Media storage and CDN for all uploaded files (images/videos)
- **Paystack**: Nigerian payment gateway for instant online payments
- **Flutterwave**: Alternative payment gateway option

### Python Packages
- **django**: Web framework (v5.2.8)
- **channels**: WebSocket/async support for real-time features
- **daphne**: ASGI server for Django Channels
- **celery**: Distributed task queue for background jobs
- **corsheaders**: CORS handling for API requests
- **python-decouple**: Environment variable management
- **cloudinary**: Python SDK for Cloudinary integration
- **django-cloudinary-storage**: Django storage backend for Cloudinary

### Infrastructure Requirements
- **Message Broker**: Required for Celery (Redis/RabbitMQ not configured in visible code)
- **Channel Layer**: Required for Django Channels (in-memory by default, Redis recommended for production)
- **ASGI Server**: Daphne configured as default server

### Frontend Technologies
- **Template Engine**: Django Templates
- **CSS**: Custom CSS with CSS variables for theming
- **JavaScript**: Vanilla JS for WebSocket chat implementation
- **No Framework**: Pure HTML/CSS/JS approach, no React/Vue

### Database Considerations
- **Current**: SQLite (default Django database)
- **Production Needs**: PostgreSQL recommended for concurrent access and production deployment
- **Migration System**: Django migrations for schema versioning

### Payment Gateway Integration
- **Paystack Webhook**: Endpoint at `/payments/paystack/webhook/` for payment confirmations
- **Security**: CSRF exemption on webhook endpoint, signature verification recommended
- **Offline Flow**: Upload proof → admin verifies → registration confirmed

### Media Delivery
- **Cloudinary CDN**: All media served through Cloudinary URLs
- **Video Storage**: Match highlights stored on Cloudinary
- **Image Optimization**: Automatic optimization through Cloudinary transformations

## Recent Enhancements (Session 2)

### Frontend Pages Completed
1. **Player Dashboard** - Enhanced with complete statistics (tournaments, matches, win rate, achievements, upcoming matches)
2. **Team Profile** - Shows team stats with win rate calculation, recent matches, and trophies count
3. **Player Profile** - Rich display with achievements, team details, and bio with golden theme styling
4. **Leaderboards** - New comprehensive page showing:
   - Top Teams by Points (standings-based ranking)
   - Top Scorers (players ranked by goals scored in tournaments)
   - Top Players by Achievements (gamification metrics)
5. **Highlights Gallery** - Public verification gallery with filter and status badges
6. **Community Chat** - WebSocket-enabled community room for friendly match posting

### Design System & Theming
- **Golden Gaming Theme**: Complete site-wide consistency with CSS variables:
  - Primary Gold: #FFD700
  - Accent Orange: #FF8C00
  - Dark backgrounds (#1a1a2e, #16213e) with light shining gold accents
  - No dark/dim aesthetic - light, shining, and professional
- **Animation**: Smooth transitions, hover effects, and glow shadows throughout
- **Navigation**: Enhanced navbar with Leaderboards link added to main menu
- **Responsive Design**: Mobile-first approach with media queries for all breakpoints

### Template Updates
- **Edit Profile Page**: Updated from purple to golden theme
- **Tournament Detail**: Flashscore-style standings table with form indicators
- **Tournament List**: Active/completed tournament sections with golden cards
- **All Pages**: Consistent use of CSS variables for theming

### View Enhancements
- **Team Profile View**: Added win_rate and trophies_count calculations
- **Player Dashboard View**: Comprehensive statistics and upcoming matches logic
- **Leaderboards View**: Three separate ranking systems with database optimization
- **Navigation**: Added leaderboards route and menu link

## Testing Status

### Completed & Verified
- Server runs without errors (no system checks issues)
- All views load successfully with proper data
- Golden theme applied site-wide
- Navigation links working correctly
- Payment field (payment_verified) confirmed in TournamentRegistration model

### Pending Tests
- Complete tournament registration + payment flow (Paystack/Flutterwave)
- Match readiness and code creation flow
- Highlight upload and verification workflow
- Automatic fixture generation when tournament fills
- Automatic achievement awarding on tournament completion
- Mobile responsiveness across all devices
- Chat WebSocket connection stability