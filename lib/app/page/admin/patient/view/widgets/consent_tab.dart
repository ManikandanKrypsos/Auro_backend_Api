import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class ConsentTab extends StatelessWidget {
  const ConsentTab({super.key});

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
              border: Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Row(
              children: [
                _summaryCell('3', 'SIGNED'),
                Container(
                  width: 0.5,
                  height: 36,
                  color: ColorResources.borderColor,
                ),
                _summaryCell('1', 'PENDING'),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // ── Add button ───────────────────────────────
          GestureDetector(
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
                  Text(
                    'ADD CONSENT FORM',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.0,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          Text(
            'CONSENT RECORDS',
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 11,
              color: ColorResources.liteTextColor,
              letterSpacing: 3.5,
            ),
          ),

          const SizedBox(height: 16),

          _card(
            title: 'General Treatment Consent',
            date: '12 Jan 2025',
            file: 'general_consent_jan25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Photography & Media Release',
            date: '12 Jan 2025',
            file: 'media_release_jan25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Dermapen Consent',
            date: '10 Mar 2025',
            file: 'dermapen_consent_mar25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Chemical Peel Consent',
            date: '—',
            file: 'chemical_peel_consent.pdf',
            isSigned: false,
            patientSigned: false,
            therapistConfirmed: false,
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  // ── Summary cell — both use primaryColor ────────────────
  Widget _summaryCell(String value, String label) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
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
  }

  // ── Consent card ────────────────────────────────────────
  Widget _card({
    required String title,
    required String date,
    required String file,
    required bool isSigned,
    required bool patientSigned,
    required bool therapistConfirmed,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        children: [
          // ── Header ──────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Row(
              children: [
                Icon(
                  isSigned
                      ? Icons.check_circle_outline
                      : Icons.radio_button_unchecked,
                  color: isSigned
                      ? ColorResources.primaryColor
                      : ColorResources.liteTextColor,
                  size: 18,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 15,
                          fontWeight: FontWeight.w400,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        isSigned ? 'Signed — $date' : 'Awaiting signature',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 11,
                          fontStyle: FontStyle.italic,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
                // Status — text only, no pill
                Text(
                  isSigned ? 'SIGNED' : 'PENDING',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: isSigned
                        ? ColorResources.primaryColor
                        : ColorResources.liteTextColor,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                  ),
                ),
              ],
            ),
          ),

          Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),

          // ── File + confirmations ─────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
            child: Row(
              children: [
                // PDF chip
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: ColorResources.blackColor,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: ColorResources.borderColor,
                      width: 0.5,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.picture_as_pdf_outlined,
                        color: ColorResources.liteTextColor,
                        size: 12,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        file,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor.withOpacity(0.5),
                          fontSize: 11,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),

                const Spacer(),

                // Confirmation badges — icon + label only
                _badge('Patient', patientSigned),
                const SizedBox(width: 12),
                _badge('Therapist', therapistConfirmed),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _badge(String label, bool confirmed) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          confirmed ? Icons.check : Icons.close,
          size: 11,
          color: confirmed
              ? ColorResources.primaryColor
              : ColorResources.liteTextColor,
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: confirmed
                ? ColorResources.whiteColor.withOpacity(0.6)
                : ColorResources.liteTextColor,
            fontSize: 11,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }
}
