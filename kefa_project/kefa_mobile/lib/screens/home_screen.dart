import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // HEADER
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'WELCOME BACK',
                        style: GoogleFonts.rajdhani(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.grey,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Champion User', // Placeholder for API data
                        style: GoogleFonts.rajdhani(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    width: 45,
                    height: 45,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE60012).withOpacity(0.1),
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFFE60012), width: 2),
                    ),
                    child: const Icon(Icons.notifications_outlined, color: Colors.white),
                  ),
                ],
              ),
              
              const SizedBox(height: 30),

              // LIVE JUMBOTRON CARD
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF1A1A1A),
                      const Color(0xFF0A1F44).withOpacity(0.9),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: Colors.white.withOpacity(0.1)),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFE60012).withOpacity(0.2),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('LIVE MATCH', style: TextStyle(color: Colors.white70, fontSize: 12)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFFE60012),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            '● LIVE',
                            style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _TeamLogo('Fnatic', '3'),
                        Text(
                          'vs',
                          style: GoogleFonts.rajdhani(
                            fontSize: 24,
                            color: Colors.white24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        _TeamLogo('G2 Esports', '1'),
                      ],
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {},
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFE60012),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: const Text('WATCH STREAM'),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 30),

              // QUICK STATS
              Text(
                'YOUR SEASON',
                style: GoogleFonts.rajdhani(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 15),
              Row(
                children: [
                  Expanded(child: _StatCard('RANK', 'Gold I', Icons.shield)),
                  const SizedBox(width: 15),
                  Expanded(child: _StatCard('WINS', '42', Icons.emoji_events)),
                  const SizedBox(width: 15),
                  Expanded(child: _StatCard('WIN RATE', '68%', Icons.trending_up)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _TeamLogo(String name, String score) {
    return Column(
      children: [
        Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            color: Colors.white10,
            shape: BoxShape.circle,
          ),
          child: const Center(child: Icon(Icons.sports_esports, color: Colors.white54)),
        ),
        const SizedBox(height: 8),
        Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(
          score,
          style: GoogleFonts.rajdhani(
            fontSize: 32,
            fontWeight: FontWeight.bold,
            color: const Color(0xFFFFD700),
          ),
        ),
      ],
    );
  }

  Widget _StatCard(String label, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: const Color(0xFFE60012), size: 20),
          const SizedBox(height: 10),
          Text(
            value,
            style: GoogleFonts.rajdhani(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          Text(
            label,
            style: GoogleFonts.rajdhani(fontSize: 12, color: Colors.white54),
          ),
        ],
      ),
    );
  }
}
