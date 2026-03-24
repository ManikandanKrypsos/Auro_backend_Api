
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/add_button.dart';

class AppointmentListScreen extends StatefulWidget {
  const AppointmentListScreen({super.key});

  @override
  State<AppointmentListScreen> createState() => _AppointmentListScreenState();
}

class _AppointmentListScreenState extends State<AppointmentListScreen> {
  int _selectedTab = 0;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  static const _tabs = ['ALL', 'UPCOMING', 'COMPLETED'];

  // ── Static Data ───────────────────────────────────────
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

  // ── Filter ────────────────────────────────────────────
  List<Map<String, dynamic>> get _filtered {
    List<Map<String, dynamic>> items;
    switch (_selectedTab) {
      case 1:
        items = _appointments
            .where((a) =>
                a['status'] == 'UPCOMING' || a['status'] == 'IN SESSION')
            .toList();
        break;
      case 2:
        items = _appointments
            .where((a) => a['status'] == 'COMPLETED')
            .toList();
        break;
      default:
        items = _appointments;
    }
    if (_searchQuery.isNotEmpty) {
      items = items
          .where((a) =>
              (a['patient'] as String)
                  .toLowerCase()
                  .contains(_searchQuery.toLowerCase()) ||
              (a['treatment'] as String)
                  .toLowerCase()
                  .contains(_searchQuery.toLowerCase()))
          .toList();
    }
    return items;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: "TODAY'S APPOINTMENTS"),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),

          // ── Search ──
          AppSearchBar(
            hintText: 'Search patient or treatment...',
            controller: _searchController,
            onChanged: (v) => setState(() => _searchQuery = v),
          ),
          const SizedBox(height: 16),

          // ── Tab Row ──
          _buildTabRow(),
          const SizedBox(height: 16),

          // ── List ──
          Expanded(
            child: _filtered.isEmpty
                ? Center(
                    child: Text(
                      'NO APPOINTMENTS FOUND',
                      style: AppTextStyles.headingSmall.copyWith(
                        color: ColorResources.liteTextColor.withOpacity(0.4),
                        letterSpacing: 3,
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
                    itemCount: _filtered.length,
                    itemBuilder: (_, i) => _buildAppointmentCard(_filtered[i]),
                  ),
          ),
        ],
      ),
      floatingActionButton: AddButton(onTap: () {
        Get.toNamed(PageRoutes.bookingScreen);
      }),
    );
  }

  // ── Tab Row ───────────────────────────────────────────
  Widget _buildTabRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_tabs.length, (i) {
          final isSelected = _selectedTab == i;
          return GestureDetector(
            onTap: () => setState(() => _selectedTab = i),
            child: Padding(
              padding: EdgeInsets.only(right: i < _tabs.length - 1 ? 40 : 0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _tabs[i],
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isSelected
                          ? ColorResources.primaryColor
                          : ColorResources.liteTextColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    height: 1.5,
                    width: isSelected ? _tabs[i].length * 10.0 : 0,
                    color: ColorResources.primaryColor,
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  // ── Appointment Card (same as dashboard) ──────────────
  Widget _buildAppointmentCard(Map<String, dynamic> appt) {
    final String status = appt['status'] as String;
    final bool arrived = appt['arrived'] as bool;
    final bool isCancelled = status == 'CANCELLED';
    final bool isCompleted = status == 'COMPLETED';

    Color statusColor;
    String statusLabel;
    switch (status) {
      case 'COMPLETED':
        statusColor = ColorResources.positiveColor;
        statusLabel = 'COMPLETED';
        break;
      case 'IN SESSION':
        statusColor = ColorResources.primaryColor;
        statusLabel = 'IN SESSION';
        break;
      case 'CANCELLED':
        statusColor = ColorResources.negativeColor;
        statusLabel = 'CANCELLED';
        break;
      default:
        statusColor = ColorResources.blueColor;
        statusLabel = 'UPCOMING';
    }

    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.appointmentDetailScreen),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Card body ──
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Time + Status
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        appt['time'] as String,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: isCancelled
                              ? ColorResources.liteTextColor
                              : ColorResources.primaryColor,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(5),
                          border: Border.all(
                              color: statusColor.withOpacity(0.35), width: 0.5),
                        ),
                        child: Text(
                          statusLabel,
                          style: TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: statusColor,
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.5,
                          ),
                        ),
                      ),
                    ],
                  ),
      
                  const SizedBox(height: 14),
      
                  // Patient name
                  Text(
                    appt['patient'] as String,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isCancelled
                          ? ColorResources.liteTextColor
                          : ColorResources.whiteColor,
                      fontSize: 20,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.3,
                      decoration: isCancelled
                          ? TextDecoration.lineThrough
                          : TextDecoration.none,
                      decorationColor:
                          ColorResources.liteTextColor.withOpacity(0.4),
                    ),
                  ),
      
                  const SizedBox(height: 6),
      
                  // Treatment
                  Text(
                    appt['treatment'] as String,
                    style: AppTextStyles.bodyItalic
                        .copyWith(color: ColorResources.whiteColor),
                  ),
      
                  const SizedBox(height: 14),
      
                  // Therapist + Duration
                  Row(
                    children: [
                      _metaChip(
                          Icons.person_outline, appt['therapist'] as String),
                      const SizedBox(width: 16),
                      _metaChip(
                          Icons.timer_outlined, appt['duration'] as String),
                    ],
                  ),
                ],
              ),
            ),
      
            // ── Check-in footer ──
            if (!isCancelled)
              GestureDetector(
                onTap: isCompleted
                    ? null
                    : () => setState(() => appt['arrived'] = !arrived),
                child: Container(
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(
                          color: ColorResources.borderColor, width: 0.5),
                    ),
                    borderRadius:
                        const BorderRadius.vertical(bottom: Radius.circular(14)),
                    color: Colors.transparent,
                  ),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  child: Row(
                    children: [
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 220),
                        width: 20,
                        height: 20,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(5),
                          color: arrived
                              ? ColorResources.primaryColor
                              : Colors.transparent,
                          border: Border.all(
                            color: arrived
                                ? ColorResources.primaryColor
                                : ColorResources.borderColor,
                            width: 1.2,
                          ),
                        ),
                        child: arrived
                            ? const Icon(Icons.check,
                                size: 13, color: Colors.black)
                            : null,
                      ),
                      const SizedBox(width: 12),
                      Text(
                        arrived ? 'Patient Arrived' : 'Mark as Arrived',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: arrived
                              ? ColorResources.primaryColor
                              : ColorResources.liteTextColor.withOpacity(0.45),
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const Spacer(),
                      if (!arrived && !isCompleted)
                        Text(
                          'TAP TO CHECK IN  →',
                          style: TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color:
                                ColorResources.primaryColor.withOpacity(0.45),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.2,
                          ),
                        ),
                      if (arrived)
                        Row(
                          children: [
                            Container(
                              width: 7,
                              height: 7,
                              decoration: const BoxDecoration(
                                color: ColorResources.primaryColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              'Checked in',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color:
                                    ColorResources.primaryColor.withOpacity(0.7),
                                fontSize: 12,
                                letterSpacing: 0.3,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  // ── Meta Chip ─────────────────────────────────────────
  Widget _metaChip(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: ColorResources.whiteColor),
        const SizedBox(width: 5),
        Text(
          label,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 12,
            letterSpacing: 0.2,
          ),
        ),
      ],
    );
  }
}