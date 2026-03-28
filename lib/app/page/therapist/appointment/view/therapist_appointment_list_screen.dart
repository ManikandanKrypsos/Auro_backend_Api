import 'package:flutter/material.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/custom_appbar.dart';
import 'package:get/get.dart';
import '../../../../routes/names.dart';

class TherapistAppointmentListScreen extends StatefulWidget {
  const TherapistAppointmentListScreen({super.key});

  @override
  State<TherapistAppointmentListScreen> createState() =>
      _TherapistAppointmentListScreenState();
}

class _TherapistAppointmentListScreenState
    extends State<TherapistAppointmentListScreen> {
  int _selectedTab = 0;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  static const _tabs = ['TODAY', 'NEXT', 'COMPLETED'];

  // ── Static Data ───────────────────────────────────────
  final List<Map<String, dynamic>> _appointments = [
    {
      'time': '09:00 AM',
      'patient': 'Margot Fontaine',
      'service': 'Signature Gold Facial',
      'duration': '60 min',
      'room': 'Facial Room 1',
      'status': 'COMPLETED',
      'day': 'today',
    },
    {
      'time': '10:30 AM',
      'patient': 'Julian Sterling',
      'service': 'Deep Tissue Therapy',
      'duration': '90 min',
      'room': 'Body Room',
      'status': 'IN SESSION',
      'day': 'today',
    },
    {
      'time': '11:45 AM',
      'patient': 'Isabelle Morel',
      'service': 'Hydra-Facial Platinum',
      'duration': '45 min',
      'room': 'Facial Room 2',
      'status': 'UPCOMING',
      'day': 'today',
    },
    {
      'time': '02:30 PM',
      'patient': 'Eleanor Vance',
      'service': 'Vitamin C Infusion',
      'duration': '30 min',
      'room': 'Facial Room 1',
      'status': 'UPCOMING',
      'day': 'today',
    },
    {
      'time': '09:00 AM',
      'patient': 'Sebastian Thorne',
      'service': 'Sculptural Face Lift',
      'duration': '75 min',
      'room': 'Facial Room 2',
      'status': 'UPCOMING',
      'day': 'upcoming',
    },
    {
      'time': '11:00 AM',
      'patient': 'Damien Cross',
      'service': 'Laser Skin Rejuvenation',
      'duration': '60 min',
      'room': 'Laser Room',
      'status': 'UPCOMING',
      'day': 'upcoming',
    },
    {
      'time': '01:30 PM',
      'patient': 'Sofia Ainsworth',
      'service': 'Body Sculpt Wrap',
      'duration': '90 min',
      'room': 'Body Room',
      'status': 'UPCOMING',
      'day': 'upcoming',
    },
    {
      'time': '09:30 AM',
      'patient': 'Clara Beaumont',
      'service': 'HydraBalance',
      'duration': '60 min',
      'room': 'Facial Room 1',
      'status': 'COMPLETED',
      'day': 'completed',
    },
    {
      'time': '11:00 AM',
      'patient': 'Marcus Weil',
      'service': 'Detox Face',
      'duration': '45 min',
      'room': 'Facial Room 2',
      'status': 'COMPLETED',
      'day': 'completed',
    },
    {
      'time': '02:00 PM',
      'patient': 'Nina Thorne',
      'service': 'Glow Treatment',
      'duration': '60 min',
      'room': 'Facial Room 1',
      'status': 'COMPLETED',
      'day': 'completed',
    },
  ];

  // ── Filter ────────────────────────────────────────────
  List<Map<String, dynamic>> get _filtered {
    List<Map<String, dynamic>> items;
    switch (_selectedTab) {
      case 0:
        items = _appointments.where((a) => a['day'] == 'today').toList();
        break;
      case 1:
        items = _appointments.where((a) => a['day'] == 'upcoming').toList();
        break;
      case 2:
        items = _appointments.where((a) => a['day'] == 'completed').toList();
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
              (a['service'] as String)
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
      appBar: const CustomAppBar(title: 'MY APPOINTMENTS'),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),

          // ── Search ──
          AppSearchBar(
            hintText: 'Search patient or service...',
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
                    itemBuilder: (_, i) =>
                        _buildAppointmentCard(_filtered[i]),
                  ),
          ),
        ],
      ),
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

  // ── Appointment Card ──────────────────────────────────
  Widget _buildAppointmentCard(Map<String, dynamic> appt) {
    final String status = appt['status'] as String;
    final bool isCancelled = status == 'CANCELLED';
    final bool isCompleted = status == 'COMPLETED';

    Color statusColor;
    switch (status) {
      case 'COMPLETED':
        statusColor = ColorResources.positiveColor;
        break;
      case 'IN SESSION':
        statusColor = ColorResources.primaryColor;
        break;
      case 'CANCELLED':
        statusColor = ColorResources.negativeColor;
        break;
      default:
        statusColor = ColorResources.blueColor;
    }

    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.therapistAppointmentDetailScreen),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Time + Status ──
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
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(5),
                    border: Border.all(
                        color: statusColor.withOpacity(0.35), width: 0.5),
                  ),
                  child: Text(
                    status,
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

            // ── Patient Name ──
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
                decorationColor: ColorResources.liteTextColor.withOpacity(0.4),
              ),
            ),

            const SizedBox(height: 6),

            // ── Service Name ──
            Text(
              appt['service'] as String,
              style: AppTextStyles.bodyItalic
                  .copyWith(color: ColorResources.whiteColor),
            ),

            const SizedBox(height: 16),

            // ── Meta row: Duration + Room ──
            Row(
              children: [
                _metaChip(Icons.timer_outlined, appt['duration'] as String),
                const SizedBox(width: 20),
                _metaChip(Icons.meeting_room_outlined, appt['room'] as String),
              ],
            ),

            // ── IN SESSION indicator ──
            if (status == 'IN SESSION') ...[
              const SizedBox(height: 14),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: ColorResources.primaryColor.withOpacity(0.07),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: ColorResources.primaryColor.withOpacity(0.25),
                      width: 0.5),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: ColorResources.primaryColor,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'SESSION IN PROGRESS',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 2.0,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // ── COMPLETED checkmark ──
            if (isCompleted) ...[
              const SizedBox(height: 14),
              Row(
                children: [
                  const Icon(Icons.check_circle_outline,
                      size: 14, color: ColorResources.positiveColor),
                  const SizedBox(width: 7),
                  Text(
                    'Session completed',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.positiveColor.withOpacity(0.8),
                      fontSize: 13,
                      letterSpacing: 0.3,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    ),
  );
}

// ── Meta Chip ─────────────────────────────────────────
  Widget _metaChip(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: ColorResources.liteTextColor),
        const SizedBox(width: 5),
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor.withOpacity(0.85),
            fontSize: 12,
            letterSpacing: 0.2,
          ),
        ),
      ],
    );
  }
}
