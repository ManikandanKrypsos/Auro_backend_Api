import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/alert_button.dart';

class StaffDetailScreen extends StatelessWidget {
  const StaffDetailScreen({super.key});

  // ── Static mock: change to false to test Receptionist view ──
  static const bool _isTherapist = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(title: 'STAFF DETAIL'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // ── Avatar ─────────────────────────────────────
              Center(
                child: Container(
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: ColorResources.primaryColor,
                      width: 2,
                    ),
                  ),
                  child: CircleAvatar(
                    radius: 64,
                    backgroundColor: ColorResources.cardColor,
                    backgroundImage: const NetworkImage(
                      'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
                    ),
                    onBackgroundImageError: (_, __) {},
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // ── Name & Role ────────────────────────────────
              Center(
                child: Column(
                  children: [
                    const Text(
                      'Julianne Sterling',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 28,
                        fontWeight: FontWeight.w300,
                        fontStyle: FontStyle.italic,
                        letterSpacing: 1.0,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'LEAD AESTHETICIAN',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 3.0,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'AURA LUXURY CLINIC',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor.withOpacity(0.35),
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 2.5,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),

              // ── Stats Row ──────────────────────────────────
              const Row(
                children: [
                  _StatBox(icon: Icons.star, value: '4.9', label: 'RATING'),
                  SizedBox(width: 12),
                  _StatBox(
                      icon: Icons.group_outlined,
                      value: '1.2k+',
                      label: 'CLIENTS'),
                  SizedBox(width: 12),
                  _StatBox(
                      icon: Icons.access_time_outlined,
                      value: '8 Yrs',
                      label: 'EXP.'),
                ],
              ),

              const SizedBox(height: 32),

              // ── Contact Information ────────────────────────
              const _SectionHeader(label: 'CONTACT INFORMATION'),
              const SizedBox(height: 16),
              Container(
                decoration: BoxDecoration(
                  color: ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                      color: ColorResources.borderColor, width: 0.5),
                ),
                child: Column(
                  children: [
                    const _ContactRow(
                      icon: Icons.mail_outline,
                      label: 'EMAIL',
                      value: 'j.sterling@auraclinic.com',
                    ),
                    _divider(),
                    const _ContactRow(
                      icon: Icons.phone_outlined,
                      label: 'PHONE',
                      value: '+1 (555) 234-8890',
                    ),
                    _divider(),
                    const _ContactRow(
                      icon: Icons.location_on_outlined,
                      label: 'BASE LOCATION',
                      value: 'Beverly Hills, CA',
                    ),
                    _divider(),
                    const _ContactRow(
                      icon: Icons.calendar_today_outlined,
                      label: 'JOINING DATE',
                      value: 'March 15, 2019',
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // ── Availability (Therapist only) ──────────────
              if (_isTherapist) ...[
                const _SectionHeader(label: 'AVAILABILITY'),
                const SizedBox(height: 16),
                const _AvailabilityCard(),
                const SizedBox(height: 32),
              ],

              // ── Management ─────────────────────────────────
              // const _SectionHeader(label: 'MANAGEMENT'),
              // const SizedBox(height: 16),
              // Container(
              //   padding: const EdgeInsets.symmetric(
              //       horizontal: 16, vertical: 14),
              //   decoration: BoxDecoration(
              //     color: ColorResources.cardColor,
              //     borderRadius: BorderRadius.circular(10),
              //     border: Border.all(
              //         color: ColorResources.borderColor, width: 0.5),
              //   ),
              //   child: Row(
              //     children: [
              //       Expanded(
              //         child: Column(
              //           crossAxisAlignment: CrossAxisAlignment.start,
              //           children: [
              //             const Text(
              //               'Active Status',
              //               style: TextStyle(
              //                 fontFamily: 'CormorantGaramond',
              //                 color: ColorResources.whiteColor,
              //                 fontSize: 15,
              //                 fontWeight: FontWeight.w400,
              //               ),
              //             ),
              //             const SizedBox(height: 2),
              //             Text(
              //               'AVAILABLE FOR BOOKINGS',
              //               style: AppTextStyles.headingSmall.copyWith(
              //                 fontSize: 9,
              //                 color: ColorResources.whiteColor
              //                     .withOpacity(0.3),
              //                 letterSpacing: 1.8,
              //               ),
              //             ),
              //           ],
              //         ),
              //       ),
              //       Switch(
              //         value: true,
              //         onChanged: null,
              //         activeColor: ColorResources.primaryColor,
              //         activeTrackColor: ColorResources.primaryColor,
              //       ),
              //     ],
              //   ),
              // ),

              // const SizedBox(height: 36),

              PrimaryButton(label: 'EDIT STAFF PROFILE', onTap: () {}),
              const SizedBox(height: 24),
              AlertButton(
                onTap: () => showDeleteDialog(context),
                text: 'DELETE MEMBER',
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _divider() => Divider(
      color: ColorResources.borderColor, height: 1, thickness: 0.5);

  void showDeleteDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: ColorResources.cardColor,
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: const Text(
          'DELETE MEMBER',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 2.5,
          ),
        ),
        content: Text(
          'Are you sure you want to remove this staff member?',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor.withOpacity(0.6),
            fontSize: 14,
            height: 1.5,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'CANCEL',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor.withOpacity(0.5),
                letterSpacing: 1.5,
                fontSize: 12,
              ),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text(
              'DELETE',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.negativeColor,
                letterSpacing: 1.5,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── AVAILABILITY CARD ───────────────────────────────────────
class _AvailabilityCard extends StatelessWidget {
  const _AvailabilityCard();

  // ── Static mock data ─────────────────────────────────────
  static const Map<String, Map<String, String>?> _weekSchedule = {
    'Mon': {'start': '9:00 AM', 'end': '5:00 PM'},
    'Tue': {'start': '9:00 AM', 'end': '5:00 PM'},
    'Wed': {'start': '10:00 AM', 'end': '6:00 PM'},
    'Thu': {'start': '9:00 AM', 'end': '5:00 PM'},
    'Fri': {'start': '9:00 AM', 'end': '4:00 PM'},
    'Sat': null, // day off
    'Sun': null, // day off
  };

  static const String _breakStart = '1:00 PM';
  static const String _breakEnd   = '2:00 PM';

  static const List<Map<String, String>> _leaves = [
    {'from': 'Apr 10, 2025', 'to': 'Apr 14, 2025', 'reason': 'Annual leave'},
    {'from': 'Jun 1, 2025',  'to': 'Jun 3, 2025',  'reason': 'Personal'},
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
    
        // ── Working Days ─────────────────────────────────
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SubHeader(label: 'WORKING DAYS & HOURS'),
            const SizedBox(height: 14),
            
            // Day chips row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: _weekSchedule.entries.map((e) {
                final isOn = e.value != null;
                return _DayChip(day: e.key, isOn: isOn);
              }).toList(),
            ),
            
            const SizedBox(height: 16),
            
            // Per-day time rows (only enabled days)
            ..._weekSchedule.entries
                .where((e) => e.value != null)
                .map((e) => _DayTimeRow(
                      day: e.key,
                      start: e.value!['start']!,
                      end: e.value!['end']!,
                    )),
          ],
        ),
    
  
              const SizedBox(height: 12),
        // ── Break Time ───────────────────────────────────
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SubHeader(label: 'GLOBAL BREAK TIME'),
            const SizedBox(height: 12),
            Row(
              children: [
                _TimeChip(time: _breakStart),
                Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10),
                  child: Text(
                    '–',
                    style: TextStyle(
                      color: ColorResources.liteTextColor,
                      fontSize: 14,
                    ),
                  ),
                ),
                _TimeChip(time: _breakEnd),
               
              ],
            ),
             const SizedBox(height: 10),
                Text(
                  'applies to all working days',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 11,
                    fontStyle: FontStyle.italic,
                  ),
                ),
          ],
        ),
    
        // ── Leave Section (only if leaves exist) ─────────
        if (_leaves.isNotEmpty) ...[
              const SizedBox(height: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SubHeader(label: 'SCHEDULED LEAVES'),
              const SizedBox(height: 12),
              ..._leaves.map((l) => _LeaveRow(
                    from: l['from']!,
                    to: l['to']!,
                    reason: l['reason'] ?? '',
                  )),
            ],
          ),
        ],
      ],
    );
  }
}

// ── SUB HEADER ──────────────────────────────────────────────
class _SubHeader extends StatelessWidget {
  final String label;
  const _SubHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.start,
      children: [
     
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor,
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 2.5,
          ),
        ),
      ],
    );
  }
}

// ── DAY CHIP ────────────────────────────────────────────────
class _DayChip extends StatelessWidget {
  final String day;
  final bool isOn;
  const _DayChip({required this.day, required this.isOn});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 38,
      height: 34,
      alignment: Alignment.center,
      decoration: BoxDecoration(
       
        border: Border.all(
          color: isOn
              ? ColorResources.primaryColor
              : ColorResources.borderColor,
          width: 0.5,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        day,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: isOn
              ? ColorResources.primaryColor
              : ColorResources.liteTextColor,
          fontSize: 10,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

// ── DAY TIME ROW ────────────────────────────────────────────
class _DayTimeRow extends StatelessWidget {
  final String day;
  final String start;
  final String end;
  const _DayTimeRow(
      {required this.day, required this.start, required this.end});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 30,
            child: Text(
              day,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 1,
              ),
            ),
          ),
          const SizedBox(width: 10),
          _TimeChip(time: start),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Text('–',
                style: TextStyle(
                    color: ColorResources.liteTextColor,
                    fontSize: 13)),
          ),
          _TimeChip(time: end),
        ],
      ),
    );
  }
}

// ── TIME CHIP ───────────────────────────────────────────────
class _TimeChip extends StatelessWidget {
  final String time;
  const _TimeChip({required this.time});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        border: Border.all(
            color: ColorResources.borderColor, width: 0.5),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.access_time_rounded,
              size: 11, color: ColorResources.primaryColor),
          const SizedBox(width: 4),
          Text(
            time,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 14,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}

// ── LEAVE ROW ───────────────────────────────────────────────
class _LeaveRow extends StatelessWidget {
  final String from;
  final String to;
  final String reason;
  const _LeaveRow(
      {required this.from, required this.to, required this.reason});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(Icons.event_busy_outlined,
              size: 14, color: ColorResources.primaryColor),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$from  –  $to',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 14,
                    letterSpacing: 0.3,
                  ),
                ),
                if (reason.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    reason,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor,
                      fontSize: 12,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── STAT BOX ────────────────────────────────────────────────
class _StatBox extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _StatBox({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(10),
          border:
              Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          children: [
            Icon(icon, color: ColorResources.primaryColor, size: 18),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 20,
                fontWeight: FontWeight.w400,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTextStyles.headingSmall.copyWith(
                fontSize: 9,
                color: ColorResources.whiteColor.withOpacity(0.35),
                letterSpacing: 2.0,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── CONTACT ROW ─────────────────────────────────────────────
class _ContactRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ContactRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.25),
                width: 0.5,
              ),
            ),
            child: Icon(icon,
                color: ColorResources.primaryColor, size: 16),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTextStyles.headingSmall.copyWith(
                  fontSize: 9,
                  color: ColorResources.whiteColor.withOpacity(0.3),
                  letterSpacing: 1.8,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── SECTION HEADER ──────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: AppTextStyles.headingSmall.copyWith(
        fontSize: 11,
        color: ColorResources.whiteColor,
        letterSpacing: 3.5,
      ),
    );
  }
}