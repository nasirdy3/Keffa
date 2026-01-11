import 'package:flutter/material.dart';

class TournamentsScreen extends StatelessWidget {
  const TournamentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('TOURNAMENTS')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.emoji_events_outlined, size: 80, color: Colors.white24),
            const SizedBox(height: 20),
            const Text('Brackets Loading...', style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 20),
            // Placeholder for Bracket Widget
            Container(
              margin: const EdgeInsets.all(20),
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFE60012).withOpacity(0.5)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Center(child: Text('Interactive Bracket View')),
            ),
          ],
        ),
      ),
    );
  }
}
