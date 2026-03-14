import 'package:flutter/material.dart';
import 'package:focusai_monitor/screens/dashboard_screen.dart';

void main() {
  runApp(const FocusAIApp());
}

class FocusAIApp extends StatelessWidget {
  const FocusAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FocusAI PRO MONITOR',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF3fb950),
        scaffoldBackgroundColor: const Color(0xFF0f1117),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3fb950),
          surface: Color(0xFF161b22),
          onSurface: Color(0xFFe6edf3),
        ),
      ),
      home: const DashboardScreen(),
    );
  }
}
