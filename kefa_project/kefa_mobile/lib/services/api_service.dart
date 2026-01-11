import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // CONFIGURATION
  // For Android Emulator, use 10.0.2.2. For Physical Device, use your PC's Local IP (e.g., 192.168.1.5).
  // For Production, use 'https://kefa-platform.onrender.com'
  static const String baseUrl = 'http://10.0.2.2:8000'; 
  
  // ENDPOINTS
  static const String loginUrl = '$baseUrl/api/auth/login/';
  static const String profileUrl = '$baseUrl/api/players/profile/me/';
  static const String matchesUrl = '$baseUrl/api/matches/live/';

  // AUTHENTICATION
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse(loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token']; // Assumes DRF returns { 'token': 'xyz' }
        
        // Save Token locally
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        
        return {'success': true, 'data': data};
      } else {
        return {'success': false, 'error': 'Invalid Credentials'};
      }
    } catch (e) {
      return {'success': false, 'error': 'Connection Error: $e'};
    }
  }

  // DATA FETCHING
  Future<Map<String, dynamic>?> getPlayerProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');

    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse(profileUrl),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Api Error: $e');
    }
    return null;
  }
}
