import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class HistoryTab extends StatelessWidget {
  const HistoryTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Summary strip ────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Row(
              children: [
                _summaryCell('3', 'COMPLETED'),
                Container(
                    width: 0.5,
                    height: 36,
                    color: ColorResources.borderColor),
                _summaryCell('1', 'CANCELLED'),
                Container(
                    width: 0.5,
                    height: 36,
                    color: ColorResources.borderColor),
                _summaryCell('1', 'SCHEDULED'),
              ],
            ),
          ),

          const SizedBox(height: 24),

          Text('TREATMENT TIMELINE',
              style: AppTextStyles.headingSmall.copyWith(
                fontSize: 11,
                color: ColorResources.liteTextColor,
                letterSpacing: 3.5,
              )),

          const SizedBox(height: 16),

          _item(
            name: 'Detox Face',
            isFace: true,
            status: 'COMPLETED',
            date: '10 Mar 2025',
            therapist: 'Anna Sterling',
            duration: '60 min',
            price: '\$120',
            session: '1 of 6',
            rating: '4.5 / 5',
            nextSession: '25 Mar 2025',
            isLast: false,
          ),
          _item(
            name: 'HydraBalance',
            isFace: true,
            status: 'COMPLETED',
            date: '25 Mar 2025',
            therapist: 'Maria Voss',
            duration: '75 min',
            price: '\$150',
            session: '2 of 6',
            rating: '5.0 / 5',
            nextSession: '10 Apr 2025',
            isLast: false,
          ),
          _item(
            name: 'Detox Face',
            isFace: true,
            status: 'COMPLETED',
            date: '10 Apr 2025',
            therapist: 'Anna Sterling',
            duration: '60 min',
            price: '\$120',
            session: '3 of 6',
            rating: '4.8 / 5',
            nextSession: '28 Apr 2025',
            isLast: false,
          ),
          _item(
            name: 'Hydra Facial Body',
            isFace: false,
            status: 'CANCELLED',
            date: '28 Apr 2025',
            therapist: 'Sienna Thorne',
            duration: '90 min',
            price: '\$200',
            session: '1 of 4',
            rating: null,
            nextSession: '12 May 2025',
            isLast: false,
          ),
          _item(
            name: 'Glow Treatment',
            isFace: true,
            status: 'SCHEDULED',
            date: '20 May 2025',
            therapist: 'Anna Sterling',
            duration: '45 min',
            price: '\$95',
            session: '1 of 3',
            rating: null,
            nextSession: '10 Jun 2025',
            isLast: true,
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  // ── Summary cell — all use primaryColor, numbers differ in opacity ──
  Widget _summaryCell(String value, String label) {
    return Expanded(
      child: Column(
        children: [
          Text(value,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 22,
                fontWeight: FontWeight.w600,
              )),
          const SizedBox(height: 2),
          Text(label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 9,
                letterSpacing: 1.5,
                fontWeight: FontWeight.w600,
              )),
        ],
      ),
    );
  }

  // ── Status helpers — only CANCELLED is red, rest use white/gold ──
  Color _statusColor(String status) {
    if (status == 'CANCELLED') return ColorResources.negativeColor;
    return ColorResources.primaryColor;
  }

  // ── Timeline item ───────────────────────────────────────
  Widget _item({
    required String name,
    required bool isFace,
    required String status,
    required String date,
    required String therapist,
    required String duration,
    required String price,
    required String session,
    required String? rating,
    required String nextSession,
    required bool isLast,
  }) {
    final dotColor = _statusColor(status);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Spine
          SizedBox(
            width: 32,
            child: Column(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  margin: const EdgeInsets.only(top: 5),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: dotColor.withOpacity(0.25),
                    border: Border.all(color: dotColor, width: 1.5),
                  ),
                ),
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

          // Card
          Expanded(
            child: Container(
              margin: const EdgeInsets.only(bottom: 14),
              decoration: BoxDecoration(
                color: ColorResources.cardColor,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                    color: ColorResources.borderColor, width: 0.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Card header ──────────────────────
                  Padding(
                    padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
                    child: Row(
                      children: [
                        Icon(
                          isFace
                              ? Icons.face_outlined
                              : Icons.accessibility_new_outlined,
                          color: ColorResources.primaryColor,
                          size: 13,
                        ),
                        const SizedBox(width: 7),
                        Expanded(
                          child: Text(name,
                              style: const TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.whiteColor,
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.5,
                              )),
                        ),
                        // Status — plain text, no pill background
                        Row(
                          children: [
                            Container(
                              width: 5,
                              height: 5,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _statusColor(status),
                              ),
                            ),
                            const SizedBox(width: 5),
                            Text(status,
                                style: TextStyle(
                                  fontFamily: 'CormorantGaramond',
                                  color: _statusColor(status),
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 1.2,
                                )),
                          ],
                        ),
                      ],
                    ),
                  ),

                  Divider(
                      color: ColorResources.borderColor,
                      height: 1,
                      thickness: 0.5),

                  // ── Details ──────────────────────────
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      children: [
                        Row(children: [
                          _cell(Icons.calendar_today_outlined, 'DATE', date),
                          _cell(Icons.person_outline, 'THERAPIST', therapist),
                        ]),
                        const SizedBox(height: 10),
                        Row(children: [
                          _cell(Icons.timer_outlined, 'DURATION', duration),
                          _cell(Icons.attach_money_outlined, 'PRICE', price),
                        ]),
                        const SizedBox(height: 10),
                        Row(children: [
                          _cell(Icons.repeat_outlined, 'SESSION', session),
                          if (rating != null)
                            _cell(Icons.star_outline, 'RATING', rating),
                        ]),
                        const SizedBox(height: 10),
                        // Next session — subtle row, no heavy background
                        Row(
                          children: [
                            Icon(Icons.event_outlined,
                                color: ColorResources.liteTextColor, size: 11),
                            const SizedBox(width: 6),
                            Text(
                              'Next  ·  $nextSession',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.liteTextColor,
                                fontSize: 12,
                                letterSpacing: 0.5,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
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
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 9,
                    letterSpacing: 1.5,
                    fontWeight: FontWeight.w600,
                  )),
              const SizedBox(height: 2),
              Text(value,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 13,
                  )),
            ],
          ),
        ],
      ),
    );
  }
}