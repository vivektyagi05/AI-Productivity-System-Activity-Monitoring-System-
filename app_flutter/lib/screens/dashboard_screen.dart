import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  static const String apiBase = 'http://127.0.0.1:8000';
  Map<String, dynamic>? state;
  Timer? _timer;
  String? _error;

  @override
  void initState() {
    super.initState();
    fetchData();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => fetchData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> fetchData() async {
    try {
      final res = await http.get(Uri.parse('$apiBase/api/dashboard'));
      if (res.statusCode == 200) {
        setState(() {
          state = jsonDecode(res.body);
          _error = null;
        });
      } else {
        setState(() => _error = 'Server error ${res.statusCode}');
      }
    } catch (e) {
      setState(() => _error = 'Connect to backend at $apiBase');
    }
  }

  String _formatTime(int sec) {
    final h = sec ~/ 3600;
    final m = (sec % 3600) ~/ 60;
    final s = sec % 60;
    return '${h.toString().padLeft(2, '0')}:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0f1117),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.warning_amber, color: Colors.orange, size: 48),
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 8),
              const Text('Start backend: python -m uvicorn app.main:app --port 8000',
                  style: TextStyle(color: Colors.white54, fontSize: 12)),
            ],
          ),
        ),
      );
    }

    final s = state ?? {};
    return Scaffold(
      backgroundColor: const Color(0xFF0f1117),
      appBar: AppBar(
        title: const Text('FocusAI PRO MONITOR'),
        backgroundColor: const Color(0xFF161b22),
        foregroundColor: const Color(0xFF3fb950),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _statusChip(s['system_state'] == 'idle' ? 'IDLE' : 'ACTIVE',
                    s['system_state'] == 'idle' ? Colors.orange : Colors.green),
                const SizedBox(width: 12),
                _statusChip('Threat: ${(s['threat_level'] ?? 'low').toString().toUpperCase()}',
                    s['threat_level'] == 'high' ? Colors.red : Colors.green),
                const SizedBox(width: 12),
                Text('Session: ${_formatTime(s['session_time_sec'] ?? 0)}',
                    style: const TextStyle(color: Colors.white70)),
              ],
            ),
            const SizedBox(height: 24),
            Card(
              color: const Color(0xFF161b22),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Text('Focus Score', style: TextStyle(color: Colors.grey[400])),
                    Text('${s['focus_score'] ?? 0}%',
                        style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Color(0xFF3fb950))),
                    Text('Grade ${s['productivity_grade'] ?? '-'}',
                        style: const TextStyle(color: Color(0xFF3fb950))),
                    const SizedBox(height: 8),
                    Text(s['ai_suggestion'] ?? 'Initializing...',
                        style: TextStyle(color: Colors.grey[400])),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                _metricCard('CPU', '${s['cpu_usage'] ?? 0}%'),
                const SizedBox(width: 12),
                _metricCard('RAM', '${s['ram_usage'] ?? 0}%'),
                const SizedBox(width: 12),
                _metricCard('Upload', _formatBytes(s['network_upload'] ?? 0)),
                const SizedBox(width: 12),
                _metricCard('Download', _formatBytes(s['network_download'] ?? 0)),
              ],
            ),
            const SizedBox(height: 20),
            if ((s['alerts'] as List?)?.isNotEmpty == true)
              Card(
                color: const Color(0xFF161b22),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Alerts', style: TextStyle(fontWeight: FontWeight.bold)),
                      ...(s['alerts'] as List).take(5).map((a) => Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(a['message'] ?? '', style: const TextStyle(color: Colors.white70)),
                      )),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _statusChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(color: color.withOpacity(0.2), borderRadius: BorderRadius.circular(20)),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w500)),
    );
  }

  Widget _metricCard(String label, String value) {
    return Expanded(
      child: Card(
        color: const Color(0xFF161b22),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(label, style: TextStyle(color: Colors.grey[400], fontSize: 12)),
              const SizedBox(height: 4),
              Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }
}
