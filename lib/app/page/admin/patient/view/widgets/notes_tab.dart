import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class NotesTab extends StatelessWidget {
  const NotesTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Add button ───────────────────────────────
          _addButton('ADD CLINICAL NOTE'),
          const SizedBox(height: 20),

          // ── Note 1 ───────────────────────────────────
          _noteCard(
            treatmentRef: 'Detox Face',
            date: '10 Mar 2025',
            therapist: 'Anna Sterling',
            skinCondition:
                'Skin slightly dehydrated with mild congestion around T-zone. No active breakouts.',
            concerns: const ['Dryness', 'Uneven texture', 'Mild pigmentation'],
            reaction:
                'Tolerated treatment well. Mild redness subsided within 20 minutes.',
            advice:
                'Avoid sun exposure for 48 hours. Use SPF 50+ daily. No exfoliation for 3 days.',
            nextTreatment: 'HydraBalance — in 2–3 weeks',
            products: const ['Hydrating serum', 'SPF 50+ sunscreen', 'Gentle cleanser'],
          ),

          // ── Note 2 ───────────────────────────────────
          _noteCard(
            treatmentRef: 'HydraBalance',
            date: '25 Mar 2025',
            therapist: 'Maria Voss',
            skinCondition:
                'Improved hydration from last session. Minor congestion remains. Overall skin tone more even.',
            concerns: const ['Acne scarring', 'Dryness'],
            reaction: 'No adverse reaction. Skin visibly plumped post-treatment.',
            advice: 'Continue using recommended serum twice daily. Avoid harsh actives.',
            nextTreatment: 'Detox Face — Session 3 of 6 in 2 weeks',
            products: const ['Vitamin C serum', 'Niacinamide moisturiser'],
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  // ── Add button ──────────────────────────────────────────
  Widget _addButton(String label) {
    return GestureDetector(
      onTap: () {},
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: ColorResources.primaryColor.withOpacity(0.4),
            width: 0.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.add, color: ColorResources.primaryColor, size: 14),
            const SizedBox(width: 8),
            Text(label,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 2.0,
                )),
          ],
        ),
      ),
    );
  }

  // ── Note card ───────────────────────────────────────────
  Widget _noteCard({
    required String treatmentRef,
    required String date,
    required String therapist,
    required String skinCondition,
    required List<String> concerns,
    required String reaction,
    required String advice,
    required String nextTreatment,
    required List<String> products,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
            child: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                        color: ColorResources.primaryColor.withOpacity(0.25),
                        width: 0.5),
                  ),
                  child: const Icon(Icons.note_outlined,
                      color: ColorResources.primaryColor, size: 16),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(treatmentRef,
                        style: const TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.5,
                        )),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Text(date,
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.liteTextColor,
                              fontSize: 11,
                            )),
                        Text('  ·  $therapist',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.primaryColor,
                              fontSize: 11,
                              fontStyle: FontStyle.italic,
                            )),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),

          Divider(
              color: ColorResources.borderColor, height: 1, thickness: 0.5),

          // Body
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _noteRow('SKIN CONDITION',
                    Text(skinCondition, style: _bodyStyle())),
                const SizedBox(height: 14),
                _noteRow('CONCERNS',
                    Wrap(spacing: 6, runSpacing: 6,
                        children: concerns.map((c) => _chip(c)).toList())),
                const SizedBox(height: 14),
                _noteRow('REACTION', Text(reaction, style: _bodyStyle())),
                const SizedBox(height: 14),
                _noteRow('ADVICE GIVEN', Text(advice, style: _bodyStyle())),
                const SizedBox(height: 14),
                _noteRow(
                  'NEXT TREATMENT',
                  Text(nextTreatment,
                      style: _bodyStyle().copyWith(
                          color: ColorResources.primaryColor,
                          fontStyle: FontStyle.italic)),
                ),
                const SizedBox(height: 14),
                _noteRow('PRODUCTS',
                    Wrap(spacing: 6, runSpacing: 6,
                        children: products
                            .map((p) => _chip(p,
                                color: ColorResources.primaryColor))
                            .toList())),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _noteRow(String label, Widget child) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 9,
              color: ColorResources.liteTextColor,
              letterSpacing: 2.0,
            )),
        const SizedBox(height: 5),
        child,
      ],
    );
  }

  Widget _chip(String label, {Color? color}) {
    final c = color ?? ColorResources.liteTextColor;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.08),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: c.withOpacity(0.3), width: 0.5),
      ),
      child: Text(label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: c,
            fontSize: 11,
            letterSpacing: 0.5,
            fontWeight: FontWeight.w500,
          )),
    );
  }

  TextStyle _bodyStyle() => TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor.withOpacity(0.75),
        fontSize: 14,
        height: 1.5,
        letterSpacing: 0.2,
      );
}