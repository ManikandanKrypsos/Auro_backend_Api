import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class _TreatmentRecord {
  final String name;
  final String category; 
  final String status;   
  final String date;
  final String therapist;
  final String duration;
  final String price;
  final String packageName;
  final String session;      
  final String? rating;       
  final String? nextSession;  
  final String? cancelReason; 

  const _TreatmentRecord({
    required this.name,
    required this.category,
    required this.status,
    required this.date,
    required this.therapist,
    required this.duration,
    required this.price,
    required this.packageName,
    required this.session,
    this.rating,
    this.nextSession,
    this.cancelReason,
  });
}

// ── Static data ────────────────────────────────────────────
const List<_TreatmentRecord> _records = [
  _TreatmentRecord(
    name: 'Detox Face',
    category: 'face',
    status: 'COMPLETED',
    date: '10 Mar 2025',
    therapist: 'Anna Sterling',
    duration: '60 min',
    price: '\$120',
    packageName: 'Detox Face Pack',
    session: '1 of 6',
    rating: '4.5 / 5',
    nextSession: '25 Mar 2025',
  ),
  _TreatmentRecord(
    name: 'HydraBalance',
    category: 'face',
    status: 'COMPLETED',
    date: '25 Mar 2025',
    therapist: 'Maria Voss',
    duration: '75 min',
    price: '\$150',
    packageName: 'HydraBalance Pack',
    session: '2 of 6',
    rating: '5.0 / 5',
    nextSession: '10 Apr 2025',
  ),
  _TreatmentRecord(
    name: 'Detox Face',
    category: 'face',
    status: 'COMPLETED',
    date: '10 Apr 2025',
    therapist: 'Anna Sterling',
    duration: '60 min',
    price: '\$120',
    packageName: 'Detox Face Pack',
    session: '3 of 6',
    rating: '4.8 / 5',
    nextSession: '28 Apr 2025',
  ),
  _TreatmentRecord(
    name: 'Hydra Facial Body',
    category: 'body',
    status: 'CANCELLED',
    date: '28 Apr 2025',
    therapist: 'Sienna Thorne',
    duration: '90 min',
    price: '\$200',
    packageName: 'Body Glow Pack',
    session: '1 of 4',
    cancelReason: 'Patient rescheduled — personal reasons',
  ),
  _TreatmentRecord(
    name: 'Crystal Frax',
    category: 'laser',
    status: 'NO SHOW',
    date: '05 May 2025',
    therapist: 'Anna Sterling',
    duration: '50 min',
    price: '\$180',
    packageName: 'Crystal Frax Pack',
    session: '1 of 3',
    cancelReason: 'Patient did not attend — no contact',
  ),
  _TreatmentRecord(
    name: 'Glow Treatment',
    category: 'face',
    status: 'SCHEDULED',
    date: '20 May 2025',
    therapist: 'Anna Sterling',
    duration: '45 min',
    price: '\$95',
    packageName: 'Glow Treatment Pack',
    session: '1 of 3',
    nextSession: '10 Jun 2025',
  ),
];

// ── HistoryTab ─────────────────────────────────────────────
class HistoryTab extends StatelessWidget {
  const HistoryTab({super.key});

  // ── Status color map ─────────────────────────────────────
  static Color statusColor(String status) {
    switch (status) {
      case 'COMPLETED':
        return const Color(0xFF5C7A5C); // muted green
      case 'CANCELLED':
        return ColorResources.negativeColor; // red
      case 'NO SHOW':
        return const Color(0xFFB07040); // amber/orange
      case 'SCHEDULED':
        return ColorResources.primaryColor; // gold
      default:
        return ColorResources.liteTextColor;
    }
  }

  // ── Category icon map ─────────────────────────────────────
  static IconData categoryIcon(String category) {
    switch (category) {
      case 'face':
        return Icons.face_outlined;
      case 'body':
        return Icons.accessibility_new_outlined;
      case 'laser':
        return Icons.flash_on_outlined;
      default:
        return Icons.spa_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Computed counts from actual data
    final completed = _records.where((r) => r.status == 'COMPLETED').length;
    final cancelled = _records.where((r) => r.status == 'CANCELLED').length;
    final noShow = _records.where((r) => r.status == 'NO SHOW').length;
    final scheduled = _records.where((r) => r.status == 'SCHEDULED').length;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Summary strip ─────────────────────────
          _SummaryStrip(
            completed: completed,
            cancelled: cancelled,
            noShow: noShow,
            scheduled: scheduled,
          ),

          const SizedBox(height: 24),

          // ── Section label ──────────────────────────
          Text(
            'TREATMENT TIMELINE',
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 11,
              color: ColorResources.liteTextColor,
              letterSpacing: 3.5,
            ),
          ),

          const SizedBox(height: 16),

          // ── Timeline items ─────────────────────────
          ...List.generate(_records.length, (i) {
            return _TimelineItem(
              record: _records[i],
              isLast: i == _records.length - 1,
            );
          }),

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ── Summary Strip ──────────────────────────────────────────
class _SummaryStrip extends StatelessWidget {
  final int completed;
  final int cancelled;
  final int noShow;
  final int scheduled;

  const _SummaryStrip({
    required this.completed,
    required this.cancelled,
    required this.noShow,
    required this.scheduled,
  });

  @override
  Widget build(BuildContext context) {
    final total = completed + cancelled + noShow + scheduled;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        children: [
          _cell('$total', 'TOTAL', ColorResources.primaryColor),
          _divider(),
          _cell('$completed', 'COMPLETED', const Color(0xFF5C7A5C)),
          _divider(),
          _cell('$cancelled', 'CANCELLED', ColorResources.negativeColor),
          _divider(),
          _cell('$scheduled', 'SCHEDULED', ColorResources.primaryColor),
        ],
      ),
    );
  }

  Widget _cell(String value, String label, Color color) => Expanded(
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: color,
                fontSize: 22,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 9,
                letterSpacing: 1.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      );

  Widget _divider() => Container(
        width: 0.5,
        height: 36,
        color: ColorResources.borderColor,
      );
}

// ── Timeline Item ──────────────────────────────────────────
class _TimelineItem extends StatelessWidget {
  final _TreatmentRecord record;
  final bool isLast;

  const _TimelineItem({required this.record, required this.isLast});

  Color get _dotColor => HistoryTab.statusColor(record.status);

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Spine ────────────────────────────────
          SizedBox(
            width: 32,
            child: Column(
              children: [
                // Dot
                Container(
                  width: 10,
                  height: 10,
                  margin: const EdgeInsets.only(top: 5),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _dotColor.withOpacity(0.2),
                    border: Border.all(color: _dotColor, width: 1.5),
                  ),
                ),
                // Connecting line
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 0.5,
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      color: ColorResources.borderColor,
                    ),
                  ),
              ],
            ),
          ),

          // ── Card ─────────────────────────────────
          Expanded(
            child: Container(
              margin: const EdgeInsets.only(bottom: 14),
              decoration: BoxDecoration(
                color: ColorResources.cardColor,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: record.status == 'SCHEDULED'
                      ? ColorResources.primaryColor.withOpacity(0.3)
                      : ColorResources.borderColor,
                  width: 0.5,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  Divider(
                      color: ColorResources.borderColor,
                      height: 1,
                      thickness: 0.5),
                  _buildBody(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Card header ────────────────────────────────────────
  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
      child: Row(
        children: [
          Icon(
            HistoryTab.categoryIcon(record.category),
            color: ColorResources.primaryColor,
            size: 13,
          ),
          const SizedBox(width: 7),
          Expanded(
            child: Text(
              record.name,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 15,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
            ),
          ),
          // Status indicator
          Row(
            children: [
              Container(
                width: 5,
                height: 5,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _dotColor,
                ),
              ),
              const SizedBox(width: 5),
              Text(
                record.status,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: _dotColor,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── Card body ──────────────────────────────────────────
  Widget _buildBody() {
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        children: [
          // Row 1 — Date + Therapist
          Row(children: [
            _cell(Icons.calendar_today_outlined, 'DATE', record.date),
            _cell(Icons.person_outline, 'THERAPIST', record.therapist),
          ]),
          const SizedBox(height: 10),

          // Row 2 — Duration + Price
          Row(children: [
            _cell(Icons.timer_outlined, 'DURATION', record.duration),
            _cell(Icons.attach_money_outlined, 'PRICE', record.price),
          ]),
          const SizedBox(height: 10),

          // Row 3 — Package + Session progress
          Row(children: [
            _cell(Icons.inventory_2_outlined, 'PACKAGE', record.packageName),
            _cell(Icons.repeat_outlined, 'SESSION', record.session),
          ]),

          // Rating row — only for completed
          if (record.status == 'COMPLETED' && record.rating != null) ...[
            const SizedBox(height: 10),
            Row(children: [
              _cell(Icons.star_outline, 'RATING', record.rating!),
              // Empty cell to keep alignment
              const Expanded(child: SizedBox()),
            ]),
          ],

          // Cancel reason — only for CANCELLED / NO SHOW
          if ((record.status == 'CANCELLED' || record.status == 'NO SHOW') &&
              record.cancelReason != null) ...[
            const SizedBox(height: 10),
            _CancelReasonRow(
              reason: record.cancelReason!,
              isNoShow: record.status == 'NO SHOW',
            ),
          ],

          // Next session — only when it makes sense
          if (record.nextSession != null &&
              record.status != 'CANCELLED' &&
              record.status != 'NO SHOW') ...[
            const SizedBox(height: 10),
            _NextSessionRow(date: record.nextSession!),
          ],
        ],
      ),
    );
  }

  Widget _cell(IconData icon, String label, String value) {
    return Expanded(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 11),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 9,
                    letterSpacing: 1.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 13,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Cancel Reason Row ──────────────────────────────────────
class _CancelReasonRow extends StatelessWidget {
  final String reason;
  final bool isNoShow;

  const _CancelReasonRow({required this.reason, required this.isNoShow});

  @override
  Widget build(BuildContext context) {
    final color = isNoShow
        ? const Color(0xFFB07040)
        : ColorResources.negativeColor;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.2), width: 0.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isNoShow ? Icons.person_off_outlined : Icons.cancel_outlined,
            size: 11,
            color: color.withOpacity(0.6),
          ),
          const SizedBox(width: 7),
          Expanded(
            child: Text(
              reason,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: color.withOpacity(0.8),
                fontSize: 12,
                fontStyle: FontStyle.italic,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Next Session Row ───────────────────────────────────────
class _NextSessionRow extends StatelessWidget {
  final String date;
  const _NextSessionRow({required this.date});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.event_outlined,
          color: ColorResources.liteTextColor,
          size: 11,
        ),
        const SizedBox(width: 6),
        Text(
          'Next  ·  $date',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor,
            fontSize: 12,
            letterSpacing: 0.5,
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }
}