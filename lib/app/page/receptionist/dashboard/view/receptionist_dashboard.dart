import 'package:aura/app/routes/names.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../main_screen/cubit/receptionist_nav_cubit.dart';

class ReceptionistDashboard extends StatefulWidget {
  const ReceptionistDashboard({super.key});

  @override
  State<ReceptionistDashboard> createState() => _ReceptionistDashboardState();
}

class _ReceptionistDashboardState extends State<ReceptionistDashboard> {
  final List<Map<String, dynamic>> _appointments = [
    {
      'time': '09:00 AM',
      'patient': 'Margot Fontaine',
      'treatment': 'Signature Gold Facial',
      'therapist': 'Dr. Elena Rodriguez',
      'duration': '60 min',
      'status': 'COMPLETED',
      'arrived': true,
    },
    {
      'time': '10:30 AM',
      'patient': 'Julian Sterling',
      'treatment': 'Deep Tissue Therapy',
      'therapist': 'Marcus Chen',
      'duration': '90 min',
      'status': 'IN SESSION',
      'arrived': true,
    },
    {
      'time': '11:45 AM',
      'patient': 'Isabelle Morel',
      'treatment': 'Hydra-Facial Platinum',
      'therapist': 'Sarah Jenkins',
      'duration': '45 min',
      'status': 'UPCOMING',
      'arrived': false,
    },
    {
      'time': '01:00 PM',
      'patient': 'Sebastian Thorne',
      'treatment': 'Sculptural Face Lift',
      'therapist': 'Dr. Elena Rodriguez',
      'duration': '75 min',
      'status': 'UPCOMING',
      'arrived': false,
    },
    {
      'time': '02:30 PM',
      'patient': 'Eleanor Vance',
      'treatment': 'Vitamin C Infusion',
      'therapist': 'Marcus Chen',
      'duration': '30 min',
      'status': 'CANCELLED',
      'arrived': false,
    },
    {
      'time': '03:45 PM',
      'patient': 'Damien Cross',
      'treatment': 'Botox — Full Face',
      'therapist': 'Sarah Jenkins',
      'duration': '45 min',
      'status': 'UPCOMING',
      'arrived': false,
    },
  ];

  @override
  Widget build(BuildContext context) {
    final upcoming = _appointments
        .where((a) => a['status'] == 'UPCOMING')
        .take(3)
        .toList();

    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: buildAppBar(context),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildGreeting(),
              const SizedBox(height: 28),
              _buildQuickStats(),
              const SizedBox(height: 28),
              _buildSectionHeader('QUICK ACTIONS'),
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,

                children: [
                  _buildQuickActionContainer(
                    icon: Icons.add_circle_outline,
                    label: 'Add\nAppointment',
                    onTap: () {
                      Get.toNamed(PageRoutes.bookingScreen);
                    },
                  ),
                  SizedBox(width: 12),
                  _buildQuickActionContainer(
                    icon: Icons.person_add_outlined,
                    label: 'Add\nPatient',
                    onTap: () {
                      Get.toNamed(PageRoutes.addPatientScreen);
                    },
                  ),
                  SizedBox(width: 12),
                  _buildQuickActionContainer(
                    icon: Icons.search_rounded,
                    label: 'Search\nPatient',
                    onTap: () {
                      context.read<ReceptionistNavCubit>().selectTab(
                        ReceptionistTab.patients,
                      );
                    },
                  ),
                ],
              ),
              const SizedBox(height: 32),
              _buildSectionHeader('NEXT UP', sub: 'Upcoming only'),
              const SizedBox(height: 16),
              ...upcoming.map((a) => _buildNextUpCard(a)),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: ColorResources.blackColor,
      elevation: 0,
      leading: const Icon(
        Icons.menu,
        color: ColorResources.whiteColor,
        size: 22,
      ),
      centerTitle: true,
      title: const Text(
        'RECEPTION',
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
            const Icon(
              Icons.notifications_outlined,
              color: ColorResources.whiteColor,
              size: 22,
            ),
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
          child: Icon(Icons.person, color: ColorResources.whiteColor, size: 18),
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
          'Sofia Laurent',
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
      {'label': "TODAY'S\nAPPOINTMENTS", 'value': '${_appointments.length}'},
      {
        'label': 'CHECKED IN',
        'value': '${_appointments.where((a) => a['arrived'] == true).length}',
      },
      {
        'label': 'CANCELLED',
        'value':
            '${_appointments.where((a) => a['status'] == 'CANCELLED').length}',
      },
      {'label': 'NEW\nPATIENTS', 'value': '3'},
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: stats
          .map(
            (s) => _buildStatCard(
              label: s['label'] as String,
              value: s['value'] as String,
            ),
          )
          .toList(),
    );
  }

  Widget _buildStatCard({required String label, required String value}) {
    return Container(
      padding: const EdgeInsets.all(16),
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
              color: ColorResources.whiteColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.8,
              height: 1.6,
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 32,
              fontWeight: FontWeight.w300,
              height: 1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionContainer({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 18),
          decoration: BoxDecoration(
            color: ColorResources.cardColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: ColorResources.borderColor, width: 0.5),
          ),
          child: Column(
            children: [
              Icon(icon, color: ColorResources.primaryColor, size: 22),
              const SizedBox(height: 10),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.3,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Next Up Card ──────────────────────────────────────
  Widget _buildNextUpCard(Map<String, dynamic> appt) {
    final parts = (appt['time'] as String).split(' ');
    final timeNum = parts[0];
    final timePeriod = parts[1];

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
                const SizedBox(height: 5),
                Text(
                  appt['treatment'] as String,
                  style: AppTextStyles.bodyItalic.copyWith(
                    color: ColorResources.whiteColor,
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    _metaChip(
                      Icons.person_outline,
                      appt['therapist'] as String,
                    ),
                    const SizedBox(width: 14),
                    _metaChip(Icons.timer_outlined, appt['duration'] as String),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Meta chip (icon + label) ──────────────────────────
  Widget _metaChip(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: ColorResources.whiteColor),
        const SizedBox(width: 5),
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 12,
            letterSpacing: 0.2,
          ),
        ),
      ],
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
              color: ColorResources.whiteColor,
              fontSize: 14,
              fontStyle: FontStyle.italic,
            ),
          ),
      ],
    );
  }
}
