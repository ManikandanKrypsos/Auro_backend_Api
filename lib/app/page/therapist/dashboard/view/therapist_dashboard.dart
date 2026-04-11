import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';

class TherapistDashboard extends StatefulWidget {
  const TherapistDashboard({super.key});

  @override
  State<TherapistDashboard> createState() => _TherapistDashboardState();
}

class _TherapistDashboardState extends State<TherapistDashboard> {
  // ── Static appointment data ───────────────────────────
  final List<Map<String, dynamic>> _appointments = [
    {
      'time': '09:00 AM',
      'patient': 'Margot Fontaine',
      'treatment': 'Signature Gold Facial',
      'duration': '60 min',
      'status': 'COMPLETED',
    },
    {
      'time': '10:30 AM',
      'patient': 'Julian Sterling',
      'treatment': 'Deep Tissue Therapy',
      'duration': '90 min',
      'status': 'COMPLETED',
    },
    {
      'time': '11:45 AM',
      'patient': 'Isabelle Morel',
      'treatment': 'Hydra-Facial Platinum',
      'duration': '45 min',
      'status': 'IN SESSION',
    },
    {
      'time': '01:00 PM',
      'patient': 'Sebastian Thorne',
      'treatment': 'Sculptural Face Lift',
      'duration': '75 min',
      'status': 'UPCOMING',
    },
    {
      'time': '02:30 PM',
      'patient': 'Eleanor Vance',
      'treatment': 'Vitamin C Infusion',
      'duration': '30 min',
      'status': 'UPCOMING',
    },
    {
      'time': '03:45 PM',
      'patient': 'Damien Cross',
      'treatment': 'Botox — Full Face',
      'duration': '45 min',
      'status': 'UPCOMING',
    },
  ];

  // ── Computed stats ────────────────────────────────────
  int get _totalToday => _appointments.length;
  int get _completed =>
      _appointments.where((a) => a['status'] == 'COMPLETED').length;
  int get _pending => _appointments
      .where((a) => a['status'] == 'UPCOMING' || a['status'] == 'IN SESSION')
      .length;

  List<Map<String, dynamic>> get _currentSession => _appointments
      .where((a) => a['status'] == 'IN SESSION')
      .toList();

  List<Map<String, dynamic>> get _upcomingList => _appointments
      .where((a) => a['status'] == 'UPCOMING')
      .toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: _buildAppBar(),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Greeting
              _buildGreeting(),
              const SizedBox(height: 28),

              // Stats
              _buildQuickStats(),
              const SizedBox(height: 32),

              // Current Session
              if (_currentSession.isNotEmpty) ...[
                _buildSectionHeader('CURRENT SESSION', sub: 'In Progress'),
                const SizedBox(height: 16),
                ..._currentSession.map((a) => _buildNextUpCard(a)),
                const SizedBox(height: 32),
              ],

              // Next Up
              if (_upcomingList.isNotEmpty) ...[
                _buildSectionHeader('NEXT UP', sub: 'Upcoming only'),
                const SizedBox(height: 16),
                ..._upcomingList.map((a) => _buildNextUpCard(a)),
              ],

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  // ── AppBar ────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: ColorResources.blackColor,
      elevation: 0,
      leading: const Icon(Icons.menu,
          color: ColorResources.whiteColor, size: 22),
      centerTitle: true,
      title: const Text(
        'MY SCHEDULE',
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor,
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 4.0,
        ),
      ),
      actions: [
        Stack(
          children: [
            const Icon(Icons.notifications_outlined,
                color: ColorResources.whiteColor, size: 22),
            Positioned(
              right: 0,
              top: 0,
              child: Container(
                width: 7,
                height: 7,
                decoration: const BoxDecoration(
                  color: ColorResources.negativeColor,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(width: 14),
        const CircleAvatar(
          radius: 14,
          backgroundColor: ColorResources.cardColor,
          child: Icon(Icons.person,
              color: ColorResources.whiteColor, size: 18),
        ),
        const SizedBox(width: 12),
      ],
    );
  }

  // ── Greeting ──────────────────────────────────────────
  Widget _buildGreeting() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Good Morning,', style: AppTextStyles.bodyItalicMedum),
        Text(
          'Sarah Jenkins',
          style: AppTextStyles.bodyItalicMedum.copyWith(fontSize: 30),
        ),
        Text(
          'Thursday, October 24, 2024',
          style: AppTextStyles.bodyItalicMedum,
        ),
      ],
    );
  }

  // ── Quick Stats ───────────────────────────────────────
  Widget _buildQuickStats() {
    final stats = [
      {
        'label': "TODAY'S\nAPPOINTMENTS",
        'value': '$_totalToday',
     
      },
      {
        'label': 'COMPLETED\nSESSIONS',
        'value': '$_completed',
       
      },
      {
        'label': 'PENDING \nSESSIONS',
        'value': '$_pending',
       
      },
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.7,
      children: stats
          .map((s) => _buildStatCard(
                label: s['label'] as String,
                value: s['value'] as String,
         
              ))
          .toList(),
    );
  }

  Widget _buildStatCard({
    required String label,
    required String value,

  }) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 16, 14, 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
        Text(
            label,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.5,
              height: 1.5,
            ),
          ),
  const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 28,
              fontWeight: FontWeight.w300,
              height: 1,
            ),
          ),
        
         
        ],
      ),
    );
  }

  // ── Next Up Card ──────────────────────────────────────
  Widget _buildNextUpCard(Map<String, dynamic> appt) {
    final parts = (appt['time'] as String).split(' ');
    final timeNum = parts[0];
    final timePeriod = parts[1];
    final bool isInSession = appt['status'] == 'IN SESSION';

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // ── Time block ──
          Container(
            width: 60,
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.2),
                width: 0.5,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  timeNum,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    height: 1,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  timePeriod,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor.withOpacity(0.7),
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 18),

          // ── Info ──
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // IN SESSION badge
                if (isInSession) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: ColorResources.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(
                          color: ColorResources.primaryColor.withOpacity(0.35),
                          width: 0.5),
                    ),
                    child: const Text(
                      'IN SESSION',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                ],

                Text(
                  appt['patient'] as String,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 18,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.2,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  appt['treatment'] as String,
                  style: AppTextStyles.bodyItalic
                      .copyWith(color: ColorResources.whiteColor),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.timer_outlined,
                        size: 12, color: ColorResources.liteTextColor),
                    const SizedBox(width: 5),
                    Text(
                      appt['duration'] as String,
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor.withOpacity(0.7),
                        fontSize: 12,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Section Header ────────────────────────────────────
  Widget _buildSectionHeader(String title, {String? sub}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: AppTextStyles.headingSmall),
        if (sub != null)
          Text(
            sub,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.5),
              fontSize: 12,
              fontStyle: FontStyle.italic,
            ),
          ),
      ],
    );
  }
}