import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import 'package:shared_preferences/shared_preferences.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  WebSocketChannel? _channel;
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, dynamic>> _messages = []; // Volatile Memory (Chapter 13 compliance)
  final ScrollController _scrollController = ScrollController();
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    _connectToChat();
  }

  Future<void> _connectToChat() async {
    // Note: Assuming no Auth middleware on WS for simplicity in prototype, 
    // or passing token in query string if supported by consumers.py
    // Emulators use 10.0.2.2 for localhost
    final wsUrl = Uri.parse('ws://10.0.2.2:8000/ws/chat/');
    
    try {
      _channel = WebSocketChannel.connect(wsUrl);
      setState(() => _isConnected = true);

      _channel!.stream.listen((message) {
        final data = jsonDecode(message);
        if (data['type'] == 'chat_message') {
          setState(() {
            _messages.add(data);
          });
          _scrollToBottom();
        }
      }, onError: (error) {
        print('WS Error: $error');
        setState(() => _isConnected = false);
      }, onDone: () {
        setState(() => _isConnected = false);
      });
    } catch (e) {
      print('Connection failed: $e');
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _sendMessage() {
    if (_controller.text.isNotEmpty && _isConnected) {
      final text = _controller.text;
      _channel?.sink.add(jsonEncode({
        'type': 'chat_message',
        'message': text,
      }));
      _controller.clear();
      // Optimistic Update
      // setState(() {
      //   _messages.add({'message': text, 'username': 'Me', 'is_me': true});
      // });
    }
  }

  @override
  void dispose() {
    _channel?.sink.close(status.goingAway);
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GLOBAL CHAT'),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: _isConnected ? Colors.green : Colors.red,
              shape: BoxShape.circle,
            ),
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isMe = msg['is_me'] ?? false;
                
                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: isMe ? const Color(0xFFE60012) : Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (!isMe)
                          Text(
                            msg['username'] ?? 'Unknown',
                            style: const TextStyle(
                              color: Color(0xFFFFD700),
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        Text(
                          msg['message'] ?? '',
                          style: const TextStyle(color: Colors.white),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.black26,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Type a message...',
                      hintStyle: const TextStyle(color: Colors.white38),
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.05),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(30),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _sendMessage,
                  icon: const Icon(Icons.send, color: Color(0xFFE60012)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
