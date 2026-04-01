import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

// ── Static session note model (ready for API later) ────────
class _SessionNote {
  final String treatmentRef;
  final String date;
  final String therapist;
  final String status;
  final String skinObservation;
  final String adviceGiven;
  final String nextTreatment;
  final List<String> productsUsed;
  final List<String> productsRecommended;
  final String? contraindictionAlert;
  final bool hasPhotos;

  const _SessionNote({
    required this.treatmentRef,
    required this.date,
    required this.therapist,
    required this.status,
    required this.skinObservation,
    required this.adviceGiven,
    required this.nextTreatment,
    required this.productsUsed,
    required this.productsRecommended,
    this.contraindictionAlert,
    this.hasPhotos = false,
  });
}

// ── Static data ────────────────────────────────────────────
const List<_SessionNote> _staticNotes = [
  _SessionNote(
    treatmentRef: 'Detox Face',
    date: '10 Mar 2025',
    therapist: 'Anna Sterling',
    status: 'COMPLETED',
    skinObservation:
        'Skin slightly dehydrated on T-zone. Mild redness on cheeks. Pores visibly congested around nose.',
    adviceGiven:
        'Avoid sun exposure for 48 hours. Use SPF 50+ daily. No exfoliation for 3 days. Keep skin moisturised.',
    nextTreatment: 'HydraBalance — in 2–3 weeks',
    productsUsed: [
      'Gentle Cleanser',
      'Hyaluronic Acid Serum',
      'Calming Rose Toner',
    ],
    productsRecommended: ['Hydrating Serum', 'SPF 50+ Sunscreen'],
    hasPhotos: true,
  ),
  _SessionNote(
    treatmentRef: 'HydraBalance',
    date: '25 Mar 2025',
    therapist: 'Maria Voss',
    status: 'COMPLETED',
    skinObservation:
        'Improved hydration from last session. Minor congestion remains on chin. Overall skin tone more even.',
    adviceGiven:
        'Continue using recommended serum twice daily. Avoid harsh actives for 5 days. No direct sun exposure.',
    nextTreatment: 'Detox Face — Session 3 of 6 · in 2 weeks',
    productsUsed: ['Vitamin C Infusion', 'Niacinamide Essence', 'SPF 50 Broad Spectrum'],
    productsRecommended: ['Vitamin C Serum', 'Niacinamide Moisturiser'],
    contraindictionAlert: 'Allergic to Salicylic Acid — avoided during session.',
    hasPhotos: true,
  ),
  _SessionNote(
    treatmentRef: 'Detox Face',
    date: '10 Apr 2025',
    therapist: 'Anna Sterling',
    status: 'COMPLETED',
    skinObservation:
        'Significant improvement in hydration. Redness reduced. Skin texture smoother compared to Session 1.',
    adviceGiven:
        'Maintain SPF routine. Begin introducing gentle exfoliant once per week. Stay hydrated.',
    nextTreatment: 'Hydra Facial Body — Session 1 of 4 · 28 Apr 2025',
    productsUsed: ['Gentle Cleanser', 'Collagen Boost Mask', 'Peptide Eye Cream'],
    productsRecommended: ['Retinol Night Cream', 'Peptide Eye Cream'],
    hasPhotos: true,
  ),
];

// ── NotesTab ───────────────────────────────────────────────
class NotesTab extends StatefulWidget {
  const NotesTab({super.key});

  @override
  State<NotesTab> createState() => _NotesTabState();
}

class _NotesTabState extends State<NotesTab> {
  // Track which cards are expanded
  final Set<int> _expanded = {0}; // first card open by default

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Summary strip ──────────────────────────
          _SummaryStrip(notes: _staticNotes),

          const SizedBox(height: 20),

          // ── Section label ──────────────────────────
          Text(
            'SESSION NOTES',
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 11,
              color: ColorResources.liteTextColor,
              letterSpacing: 3.5,
            ),
          ),

          const SizedBox(height: 14),

          // ── Note cards ─────────────────────────────
          ...List.generate(_staticNotes.length, (i) {
            final note = _staticNotes[i];
            final isExpanded = _expanded.contains(i);
            return _NoteCard(
              note: note,
              isExpanded: isExpanded,
              onToggle: () => setState(() {
                if (isExpanded) {
                  _expanded.remove(i);
                } else {
                  _expanded.add(i);
                }
              }),
            );
          }),

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ── Summary strip ──────────────────────────────────────────
class _SummaryStrip extends StatelessWidget {
  final List<_SessionNote> notes;
  const _SummaryStrip({required this.notes});

  @override
  Widget build(BuildContext context) {
    final completed = notes.where((n) => n.status == 'COMPLETED').length;
    final withPhotos = notes.where((n) => n.hasPhotos).length;
    final total = notes.length;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        children: [
          _cell('$total', 'TOTAL NOTES'),
          _divider(),
          _cell('$completed', 'COMPLETED'),
          _divider(),
          _cell('$withPhotos', 'WITH PHOTOS'),
        ],
      ),
    );
  }

  Widget _cell(String value, String label) => Expanded(
        child: Column(
          children: [
            Text(
              value,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
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

// ── Note Card ──────────────────────────────────────────────
class _NoteCard extends StatelessWidget {
  final _SessionNote note;
  final bool isExpanded;
  final VoidCallback onToggle;

  const _NoteCard({
    required this.note,
    required this.isExpanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header (always visible, tappable) ──────
          GestureDetector(
            onTap: onToggle,
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
              child: Row(
                children: [
                  // Icon box
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: ColorResources.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: ColorResources.primaryColor.withOpacity(0.25),
                        width: 0.5,
                      ),
                    ),
                    child: const Icon(
                      Icons.note_outlined,
                      color: ColorResources.primaryColor,
                      size: 16,
                    ),
                  ),
                  const SizedBox(width: 12),

                  // Treatment + date + therapist
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          note.treatmentRef,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0.5,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            Text(
                              note.date,
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.liteTextColor,
                                fontSize: 11,
                              ),
                            ),
                            Text(
                              '  ·  ${note.therapist}',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.primaryColor,
                                fontSize: 11,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 8),

                  // Status badge
                  _StatusBadge(status: note.status),

                  const SizedBox(width: 10),

                  // Expand/collapse arrow
                  AnimatedRotation(
                    turns: isExpanded ? 0.5 : 0,
                    duration: const Duration(milliseconds: 200),
                    child: Icon(
                      Icons.keyboard_arrow_down_rounded,
                      color: ColorResources.liteTextColor,
                      size: 18,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // ── Expandable body ────────────────────────
          AnimatedCrossFade(
            firstChild: const SizedBox(width: double.infinity),
            secondChild: _NoteBody(note: note),
            crossFadeState: isExpanded
                ? CrossFadeState.showSecond
                : CrossFadeState.showFirst,
            duration: const Duration(milliseconds: 220),
          ),
        ],
      ),
    );
  }
}

// ── Note Body ──────────────────────────────────────────────
class _NoteBody extends StatelessWidget {
  final _SessionNote note;
  const _NoteBody({required this.note});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),

        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Contraindication alert ──────────────
              if (note.contraindictionAlert != null) ...[
                _ContraAlert(text: note.contraindictionAlert!),
                const SizedBox(height: 14),
              ],

              // ── Skin observation ────────────────────
              _noteRow(
                'SKIN OBSERVATION',
                Text(note.skinObservation, style: _bodyStyle()),
              ),
              const SizedBox(height: 14),

              _dividerLine(),
              const SizedBox(height: 14),

              // ── Advice given ────────────────────────
              _noteRow(
                'ADVICE GIVEN',
                Text(note.adviceGiven, style: _bodyStyle()),
              ),
              const SizedBox(height: 14),

              _dividerLine(),
              const SizedBox(height: 14),

              // ── Products used ───────────────────────
              _noteRow(
                'PRODUCTS USED',
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: note.productsUsed
                      .map((p) => _Chip(
                            label: p,
                            color: ColorResources.liteTextColor,
                          ))
                      .toList(),
                ),
              ),
              const SizedBox(height: 14),

              // ── Products recommended ─────────────────
              _noteRow(
                'RECOMMENDED TO PATIENT',
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: note.productsRecommended
                      .map((p) => _Chip(
                            label: p,
                            color: ColorResources.primaryColor,
                          ))
                      .toList(),
                ),
              ),
              const SizedBox(height: 14),

              _dividerLine(),
              const SizedBox(height: 14),

              // ── Next treatment ──────────────────────
              _noteRow(
                'NEXT TREATMENT',
                Text(
                  note.nextTreatment,
                  style: _bodyStyle().copyWith(
                    color: ColorResources.primaryColor,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),

              // ── Photos row ──────────────────────────
              if (note.hasPhotos) ...[
                const SizedBox(height: 14),
                _dividerLine(),
                const SizedBox(height: 14),
                _noteRow('BEFORE & AFTER', _PhotosPreviewRow()),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _noteRow(String label, Widget child) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor,
            fontSize: 9,
            letterSpacing: 2.0,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        child,
      ],
    );
  }

  Widget _dividerLine() =>
      Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5);

  TextStyle _bodyStyle() => TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor.withOpacity(0.75),
        fontSize: 14,
        height: 1.55,
        letterSpacing: 0.2,
      );
}

// ── Contraindication alert ─────────────────────────────────
class _ContraAlert extends StatelessWidget {
  final String text;
  const _ContraAlert({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: ColorResources.negativeColor.withOpacity(0.06),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: ColorResources.negativeColor.withOpacity(0.25),
          width: 0.5,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.warning_amber_rounded,
            size: 14,
            color: ColorResources.negativeColor.withOpacity(0.7),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.negativeColor.withOpacity(0.85),
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

// ── Photos preview row ─────────────────────────────────────
class _PhotosPreviewRow extends StatelessWidget {
  const _PhotosPreviewRow();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _photoThumb('BEFORE', false)),
        const SizedBox(width: 10),
        Expanded(child: _photoThumb('AFTER', true)),
      ],
    );
  }

  Widget _photoThumb(String label, bool isAfter) {
    final labelColor =
        isAfter ? ColorResources.positiveColor : ColorResources.liteTextColor;
    final borderColor = isAfter
        ? ColorResources.positiveColor.withOpacity(0.35)
        : ColorResources.borderColor;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: labelColor,
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.0,
          ),
        ),
        const SizedBox(height: 5),
        AspectRatio(
          aspectRatio: 4 / 3,
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.blackColor,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: borderColor, width: 0.5),
            ),
            child: Center(
              child: Icon(
                Icons.image_outlined,
                color: ColorResources.borderColor,
                size: 22,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ── Status badge ───────────────────────────────────────────
class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  Color get _color {
    switch (status) {
      case 'COMPLETED':
        return const Color(0xFF5C7A5C);
      case 'CANCELLED':
        return ColorResources.negativeColor;
      case 'SCHEDULED':
        return ColorResources.primaryColor;
      default:
        return ColorResources.liteTextColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: _color.withOpacity(0.35), width: 0.5),
      ),
      child: Text(
        status,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: _color,
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

// ── Chip ───────────────────────────────────────────────────
class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  const _Chip({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.3), width: 0.5),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: color,
          fontSize: 11,
          letterSpacing: 0.5,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}