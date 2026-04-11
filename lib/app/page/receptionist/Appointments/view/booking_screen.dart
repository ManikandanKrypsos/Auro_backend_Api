import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/primary_button.dart';

class BookingScreen extends StatefulWidget {
  const BookingScreen({super.key});

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  // ── Selected State ────────────────────────────────────
  Map<String, dynamic>? _selectedPatient;
  Map<String, dynamic>? _selectedService;
  Map<String, dynamic>? _selectedTherapist;
  DateTime _selectedDate = DateTime.now();
  DateTime _calendarMonth = DateTime.now();
  String? _selectedTimeSlot;
  String? _selectedRoom;
  final TextEditingController _notesController = TextEditingController();
  int _laserSession = 1;

  // ── Static Data ───────────────────────────────────────
  static const List<Map<String, dynamic>> _patients = [
    {'name': 'Maria Johnson', 'phone': '+91 98765 43210'},
    {'name': 'Isabelle Morel', 'phone': '+91 91234 56789'},
    {'name': 'Julian Sterling', 'phone': '+91 99887 76655'},
    {'name': 'Margot Fontaine', 'phone': '+91 87654 32109'},
    {'name': 'Sebastian Thorne', 'phone': '+91 76543 21098'},
    {'name': 'Eleanor Vance', 'phone': '+91 65432 10987'},
  ];

  static const List<Map<String, dynamic>> _services = [
    {'category': 'FACE', 'name': 'Detox Facial', 'duration': '45 min', 'isLaser': false},
    {'category': 'FACE', 'name': 'Glow Facial', 'duration': '60 min', 'isLaser': false},
    {'category': 'FACE', 'name': 'Gold Serum Facial', 'duration': '75 min', 'isLaser': false},
    {'category': 'BODY', 'name': 'Hydra Body Wrap', 'duration': '90 min', 'isLaser': false},
    {'category': 'BODY', 'name': 'Deep Tissue Massage', 'duration': '60 min', 'isLaser': false},
    {'category': 'LASER', 'name': 'Laser Treatment', 'duration': '30 min', 'isLaser': true, 'totalSessions': 5},
    {'category': 'LASER', 'name': 'Laser Hair Removal', 'duration': '45 min', 'isLaser': true, 'totalSessions': 6},
  ];

  static const List<Map<String, dynamic>> _therapists = [
    {'name': 'Anna Williams', 'role': 'Senior Aesthetician', 'specialties': ['FACE', 'LASER']},
    {'name': 'Sarah Jenkins', 'role': 'Esthetician', 'specialties': ['FACE', 'BODY']},
    {'name': 'Marcus Chen', 'role': 'Massage Specialist', 'specialties': ['BODY']},
    {'name': 'Dr. Elena Rodriguez', 'role': 'Lead Aesthetician', 'specialties': ['FACE', 'LASER', 'BODY']},
  ];

  static const List<String> _rooms = [
    'Facial Room 1',
    'Facial Room 2',
    'Body Room',
    'Laser Room',
  ];

  static const List<String> _timeSlots = [
    '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM',
    '11:00 AM', '11:30 AM', '12:00 PM', '01:00 PM',
    '02:00 PM', '02:30 PM', '03:00 PM', '03:30 PM',
    '04:00 PM', '05:00 PM',
  ];

  List<Map<String, dynamic>> get _filteredTherapists {
    if (_selectedService == null) return _therapists;
    final cat = _selectedService!['category'] as String;
    return _therapists.where((t) => (t['specialties'] as List).contains(cat)).toList();
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  bool get _canBook =>
      _selectedPatient != null &&
      _selectedService != null &&
      _selectedTherapist != null &&
      _selectedTimeSlot != null;

  // ── Helpers ───────────────────────────────────────────
  String _monthName(int month) {
    const m = [
      'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
      'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
    ];
    return m[month - 1];
  }

  String _dayLabel(int weekday) {
    const d = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    return d[weekday - 1];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'NEW BOOKING'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 140),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionCard(label: 'PATIENT', child: _buildPatientSection()),
            const SizedBox(height: 14),
            _buildSectionCard(label: 'SERVICE', child: _buildServiceSection()),
            const SizedBox(height: 14),
            _buildSectionCard(label: 'THERAPIST', child: _buildTherapistSection()),
            const SizedBox(height: 14),
            _buildSectionCard(label: 'ROOM', isOptional: true, child: _buildRoomSection()),
            const SizedBox(height: 14),
            _buildSectionCard(label: 'DATE', child: _buildDateTimeSection()),
            const SizedBox(height: 14),
            _buildSectionCard(label: "AVAILABLE SLOT", child: _buildSlot()),
            if (_canBook) _buildSummary(),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 36),
        child: PrimaryButton(
          label: 'CONFIRM BOOKING',
          onTap: _canBook ? () {} : () {},
        ),
      ),
    );
  }

  // ── 1️⃣ Patient Section ───────────────────────────────
  Widget _buildPatientSection() {
    if (_selectedPatient != null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: ColorResources.primaryColor.withOpacity(0.35),
            width: 0.8,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: ColorResources.primaryColor.withOpacity(0.4),
                  width: 1.5,
                ),
                color: const Color(0xFF1A1A1A),
              ),
              child: const Icon(Icons.person, color: ColorResources.liteTextColor, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _selectedPatient!['name'] as String,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 17,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _selectedPatient!['phone'] as String,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.6),
                      fontSize: 13,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: () => setState(() => _selectedPatient = null),
              child: Icon(
                Icons.close_rounded,
                size: 18,
                color: ColorResources.liteTextColor.withOpacity(0.4),
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        GestureDetector(
          onTap: () => _showPatientPicker(context),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: ColorResources.blackColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Row(
              children: [
                const Icon(Icons.search, color: ColorResources.whiteColor, size: 18),
                const SizedBox(width: 10),
                Text(
                  'Search patient...',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.25),
                    fontSize: 15,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        PrimaryButton(label: '+ ADD NEW PATIENT', onTap: () {}, vPadding: 12),
      ],
    );
  }

  // ── 2️⃣ Service Section ───────────────────────────────
  Widget _buildServiceSection() {
    final Map<String, List<Map<String, dynamic>>> grouped = {};
    for (final s in _services) {
      final cat = s['category'] as String;
      grouped[cat] = [...(grouped[cat] ?? []), s];
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ...grouped.entries.map(
          (entry) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Text(
                  entry.key,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.5),
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2.5,
                  ),
                ),
              ),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: entry.value.map((s) => _buildServiceChip(s)).toList(),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
        if (_selectedService != null && _selectedService!['isLaser'] == true) ...[
          const Divider(color: Color(0xFF2A2A2A), height: 1, thickness: 0.5),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'SESSION NUMBER',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Session $_laserSession of ${_selectedService!['totalSessions']}',
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  _sessionBtn(
                    icon: Icons.remove,
                    onTap: () {
                      if (_laserSession > 1) setState(() => _laserSession--);
                    },
                  ),
                  Container(
                    width: 44,
                    alignment: Alignment.center,
                    child: Text(
                      '$_laserSession',
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 20,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  _sessionBtn(
                    icon: Icons.add,
                    onTap: () {
                      final max = _selectedService!['totalSessions'] as int;
                      if (_laserSession < max) setState(() => _laserSession++);
                    },
                  ),
                ],
              ),
            ],
          ),
        ],
      ],
    );
  }

  Widget _buildServiceChip(Map<String, dynamic> service) {
    final bool isSelected = _selectedService == service;
    return GestureDetector(
      onTap: () => setState(() {
        _selectedService = service;
        _selectedTherapist = null;
        _laserSession = 1;
      }),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        decoration: BoxDecoration(
          color: isSelected
              ? ColorResources.primaryColor.withOpacity(0.12)
              : ColorResources.blackColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? ColorResources.primaryColor : ColorResources.borderColor,
            width: isSelected ? 0.8 : 0.5,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              service['name'] as String,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: isSelected ? ColorResources.primaryColor : ColorResources.whiteColor,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              service['duration'] as String,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor.withOpacity(0.5),
                fontSize: 10,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sessionBtn({required IconData icon, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Icon(icon, size: 16, color: ColorResources.primaryColor),
      ),
    );
  }

  // ── 3️⃣ Therapist Section ─────────────────────────────
  Widget _buildTherapistSection() {
    final therapists = _filteredTherapists;
    if (therapists.isEmpty) {
      return Text(
        'Please select a service first',
        style: AppTextStyles.bodyItalic.copyWith(fontSize: 13),
      );
    }
    return Column(
      children: therapists.map((t) => _buildTherapistRow(t)).toList(),
    );
  }

  Widget _buildTherapistRow(Map<String, dynamic> therapist) {
    final bool isSelected = _selectedTherapist == therapist;
    return GestureDetector(
      onTap: () => setState(() => _selectedTherapist = therapist),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected
              ? ColorResources.primaryColor.withOpacity(0.08)
              : ColorResources.blackColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? ColorResources.primaryColor : ColorResources.borderColor,
            width: isSelected ? 0.8 : 0.5,
          ),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 20,
              backgroundColor: ColorResources.primaryColor.withOpacity(0.1),
              child: Text(
                (therapist['name'] as String)[0],
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    therapist['name'] as String,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isSelected ? ColorResources.primaryColor : ColorResources.whiteColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Text(
                    therapist['role'] as String,
                    style: AppTextStyles.bodyItalic.copyWith(fontSize: 11),
                  ),
                ],
              ),
            ),
            if (isSelected)
              Container(
                width: 20,
                height: 20,
                decoration: const BoxDecoration(
                  color: ColorResources.primaryColor,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check, size: 12, color: Colors.black),
              ),
          ],
        ),
      ),
    );
  }

  // ── 4️⃣ Date & Time Section ───────────────────────────
  Widget _buildDateTimeSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildCalendar(),
      ]
    );
  }

  // ── Calendar ──────────────────────────────────────────
  Widget _buildCalendar() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final firstDay = DateTime(_calendarMonth.year, _calendarMonth.month, 1);
    final daysInMonth =
        DateTime(_calendarMonth.year, _calendarMonth.month + 1, 0).day;
    // Monday-based offset (Mon=1 → offset 0, Sun=7 → offset 6)
    final startOffset = (firstDay.weekday - 1) % 7;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Month navigation header ──
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Prev month
            GestureDetector(
              onTap: () => setState(() {
                _calendarMonth = DateTime(
                  _calendarMonth.year,
                  _calendarMonth.month - 1,
                );
              }),
              child: Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: ColorResources.borderColor, width: 0.5),
                ),
                child: const Icon(
                  Icons.chevron_left_rounded,
                  color: ColorResources.whiteColor,
                  size: 20,
                ),
              ),
            ),

            // Month + Year label
            Column(
              children: [
                Text(
                  _monthName(_calendarMonth.month),
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2,
                  ),
                ),
                Text(
                  '${_calendarMonth.year}',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.5),
                    fontSize: 11,
                    letterSpacing: 1,
                  ),
                ),
              ],
            ),

            // Next month
            GestureDetector(
              onTap: () => setState(() {
                _calendarMonth = DateTime(
                  _calendarMonth.year,
                  _calendarMonth.month + 1,
                );
              }),
              child: Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: ColorResources.borderColor, width: 0.5),
                ),
                child: const Icon(
                  Icons.chevron_right_rounded,
                  color: ColorResources.whiteColor,
                  size: 20,
                ),
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),

        // ── Weekday headers ──
        Row(
          children: ['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d) {
            return Expanded(
              child: Center(
                child: Text(
                  d,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.4),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1,
                  ),
                ),
              ),
            );
          }).toList(),
        ),

        const SizedBox(height: 8),

        // ── Day grid ──
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 7,
            mainAxisSpacing: 4,
            crossAxisSpacing: 2,
            childAspectRatio: 1.1,
          ),
          itemCount: startOffset + daysInMonth,
          itemBuilder: (_, index) {
            // Empty leading cells
            if (index < startOffset) return const SizedBox();

            final dayNum = index - startOffset + 1;
            final thisDate = DateTime(
              _calendarMonth.year,
              _calendarMonth.month,
              dayNum,
            );
            final isPast = thisDate.isBefore(today);
            final isToday = thisDate == today;
            final isSelected = thisDate.day == _selectedDate.day &&
                thisDate.month == _selectedDate.month &&
                thisDate.year == _selectedDate.year;

            return GestureDetector(
              onTap: isPast
                  ? null
                  : () => setState(() => _selectedDate = thisDate),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                margin: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  color: isSelected
                      ? ColorResources.primaryColor
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(8),
                  border: isToday && !isSelected
                      ? Border.all(
                          color: ColorResources.primaryColor.withOpacity(0.6),
                          width: 0.8,
                        )
                      : null,
                ),
                child: Center(
                  child: Text(
                    '$dayNum',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      fontSize: 15,
                      fontWeight: isSelected || isToday
                          ? FontWeight.w600
                          : FontWeight.w400,
                      color: isSelected
                          ? Colors.black
                          : isPast
                              ? ColorResources.liteTextColor.withOpacity(0.2)
                              : isToday
                                  ? ColorResources.primaryColor
                                  : ColorResources.whiteColor,
                    ),
                  ),
                ),
              ),
            );
          },
        ),

        const SizedBox(height: 12),

        // ── Selected date display ──
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: ColorResources.primaryColor.withOpacity(0.07),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: ColorResources.primaryColor.withOpacity(0.2),
              width: 0.5,
            ),
          ),
          child: Row(
            children: [
              Icon(
                Icons.calendar_today_outlined,
                color: ColorResources.primaryColor.withOpacity(0.7),
                size: 14,
              ),
              const SizedBox(width: 10),
              Text(
                '${_dayLabel(_selectedDate.weekday)},  '
                '${_selectedDate.day}  ${_monthName(_selectedDate.month)}  ${_selectedDate.year}',
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── 5️⃣ Room Section ──────────────────────────────────
  Widget _buildRoomSection() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _rooms.map((room) {
        final bool isSelected = (_selectedRoom ?? '') == room;
        return GestureDetector(
          onTap: () => setState(() => _selectedRoom = room),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
            decoration: BoxDecoration(
              color: isSelected
                  ? ColorResources.primaryColor.withOpacity(0.12)
                  : ColorResources.blackColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isSelected ? ColorResources.primaryColor : ColorResources.borderColor,
                width: isSelected ? 0.8 : 0.5,
              ),
            ),
            child: Text(
              room,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: isSelected ? ColorResources.primaryColor : ColorResources.whiteColor,
                fontSize: 13,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  // ── 6️⃣ Summary ───────────────────────────────────────
  Widget _buildSummary() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: ColorResources.primaryColor.withOpacity(0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: ColorResources.primaryColor.withOpacity(0.25),
          width: 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'BOOKING SUMMARY',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.primaryColor,
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 2.5,
            ),
          ),
          const SizedBox(height: 14),
          _summaryRow('Patient', _selectedPatient!['name'] as String),
          _summaryRow('Service', _selectedService!['name'] as String),
          if (_selectedService!['isLaser'] == true)
            _summaryRow('Session', '$_laserSession of ${_selectedService!['totalSessions']}'),
          _summaryRow('Therapist', _selectedTherapist!['name'] as String),
          _summaryRow(
            'Date',
            '${_dayLabel(_selectedDate.weekday)}, '
            '${_selectedDate.day} ${_monthName(_selectedDate.month)} ${_selectedDate.year}',
          ),
          if (_selectedTimeSlot != null) _summaryRow('Time', _selectedTimeSlot!),
          _summaryRow('Room', _selectedRoom ?? 'Auto Assign'),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor.withOpacity(0.5),
                fontSize: 12,
                letterSpacing: 0.5,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '·',
            style: TextStyle(
              color: ColorResources.liteTextColor.withOpacity(0.3),
              fontSize: 14,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Section Card ──────────────────────────────────────
  Widget _buildSectionCard({
    required String label,
    required Widget child,
    bool isOptional = false,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 2.5,
                ),
              ),
              if (isOptional)
                Text(
                  'Optional',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.4),
                    fontSize: 11,
                    fontStyle: FontStyle.italic,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }

  // ── Patient Picker Bottom Sheet ───────────────────────
  void _showPatientPicker(BuildContext context) {
    final TextEditingController searchCtrl = TextEditingController();
    List<Map<String, dynamic>> filtered = List.from(_patients);

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111111),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
          child: Container(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 3,
                    decoration: BoxDecoration(
                      color: ColorResources.borderColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'SELECT PATIENT',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                  decoration: BoxDecoration(
                    color: ColorResources.cardColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: ColorResources.borderColor, width: 0.5),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.search,
                        color: ColorResources.primaryColor.withOpacity(0.7),
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: searchCtrl,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 14,
                          ),
                          decoration: InputDecoration(
                            hintText: 'Search patient...',
                            hintStyle: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.whiteColor.withOpacity(0.25),
                              fontSize: 14,
                            ),
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(vertical: 10),
                          ),
                          cursorColor: ColorResources.primaryColor,
                          onChanged: (v) => setSheet(() {
                            filtered = _patients
                                .where((p) => (p['name'] as String)
                                    .toLowerCase()
                                    .contains(v.toLowerCase()))
                                .toList();
                          }),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                ...filtered.map(
                  (p) => GestureDetector(
                    onTap: () {
                      setState(() => _selectedPatient = p);
                      Navigator.pop(ctx);
                    },
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 4),
                      decoration: BoxDecoration(
                        border: Border(
                          bottom: BorderSide(color: ColorResources.borderColor, width: 0.5),
                        ),
                      ),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 16,
                            backgroundColor: ColorResources.primaryColor.withOpacity(0.1),
                            child: Text(
                              (p['name'] as String)[0],
                              style: const TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.primaryColor,
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  p['name'] as String,
                                  style: const TextStyle(
                                    fontFamily: 'CormorantGaramond',
                                    color: ColorResources.whiteColor,
                                    fontSize: 15,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                Text(
                                  p['phone'] as String,
                                  style: TextStyle(
                                    fontFamily: 'CormorantGaramond',
                                    color: ColorResources.liteTextColor.withOpacity(0.5),
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
  
  Widget _buildSlot() {

      
   return     Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _timeSlots.map((slot) {
            final bool isSelected = _selectedTimeSlot == slot;
            return GestureDetector(
              onTap: () => setState(() => _selectedTimeSlot = slot),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                decoration: BoxDecoration(
                  color: isSelected
                      ? ColorResources.primaryColor.withOpacity(0.12)
                      : ColorResources.blackColor,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isSelected ? ColorResources.primaryColor : ColorResources.borderColor,
                    width: isSelected ? 0.8 : 0.5,
                  ),
                ),
                child: Text(
                  slot,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: isSelected ? ColorResources.primaryColor : ColorResources.whiteColor,
                    fontSize: 13,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            );
          }).toList(),
        );
     
  }
}