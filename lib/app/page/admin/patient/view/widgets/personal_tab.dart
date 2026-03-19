import 'package:flutter/material.dart';

import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class PersonalTab extends StatelessWidget {
  const PersonalTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── CONTACT DETAILS ──────────────────────────────
        _SectionHeader(label: 'CONTACT DETAILS'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            children: [
              _ContactCard(
                icon: Icons.mail_outline,
                label: 'EMAIL',
                value: 'e.vance@luxurycorp.com',
              ),
              const SizedBox(height: 10),
              _ContactCard(
                icon: Icons.phone_outlined,
                label: 'PHONE',
                value: '+1 (555) 728-9102',
              ),
            ],
          ),
        ),

        const SizedBox(height: 32),

        // ── ADDRESS ──────────────────────────────────────
        _SectionHeader(label: 'ADDRESS'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                _MedicalRow(
                  label: 'CITY',
                  value: 'New York',
                  valueColor: ColorResources.whiteColor,
                ),
                _divider(),
                _MedicalRow(
                  label: 'COUNTRY',
                  value: 'United States',
                  valueColor: ColorResources.whiteColor,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── BASIC INFORMATION ────────────────────────────
        _SectionHeader(label: 'BASIC INFORMATION'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                _MedicalRow(
                  label: 'GENDER',
                  value: 'Female',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                _MedicalRow(
                  label: 'DATE OF BIRTH',
                  value: '24 April 2000',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                _MedicalRow(
                  label: 'AGE',
                  value: '24',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── MEDICAL SUMMARY ──────────────────────────────
        _SectionHeader(label: 'MEDICAL SUMMARY'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                _MedicalRow(
                  label: 'BLOOD TYPE',
                  value: 'O Positive',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                _MedicalRow(
                  label: 'ALLERGIES',
                  value: 'Penicillin, Latex',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                _MedicalRow(
                  label: 'SKIN TYPE',
                  value: 'Combination',
                  valueColor: ColorResources.negativeColor,
                  isItalic: true,
                ),
                _divider(),
                _MedicalRow(
                  label: 'CONTRAINDICATIONS',
                  value: 'None',
                  valueColor: ColorResources.negativeColor,
                  isItalic: true,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── MARKETING SOURCE ─────────────────────────────
        _SectionHeader(label: 'MARKETING SOURCE'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: const [
              _SourceChip(label: 'Instagram', icon: Icons.photo_camera_outlined, isSelected: true),
              _SourceChip(label: 'Website', icon: Icons.language_outlined),
              _SourceChip(label: 'Walk-in', icon: Icons.directions_walk_outlined),
              _SourceChip(label: 'Referral', icon: Icons.people_outline),
            ],
          ),
        ),

        const SizedBox(height: 24),
      ],
    );
  }

  Widget _divider() =>
      Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5);
}

// ── SOURCE CHIP ────────────────────────────────────────────
class _SourceChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;

  const _SourceChip({
    required this.label,
    required this.icon,
    this.isSelected = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
      decoration: BoxDecoration(
        color: isSelected
            ? ColorResources.primaryColor.withOpacity(0.12)
            : ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isSelected
              ? ColorResources.primaryColor
              : ColorResources.borderColor,
          width: 0.5,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 13,
            color: isSelected
                ? ColorResources.primaryColor
                : ColorResources.liteTextColor,
          ),
          const SizedBox(width: 7),
          Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              fontSize: 12,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.5,
              color: isSelected
                  ? ColorResources.primaryColor
                  : ColorResources.liteTextColor,
            ),
          ),
        ],
      ),
    );
  }
}

// ── SHARED WIDGETS ─────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Text(
        label,
        style: AppTextStyles.headingSmall.copyWith(
          fontSize: 11,
          color: ColorResources.liteTextColor,
          letterSpacing: 3.5,
        ),
      ),
    );
  }
}

class _ContactCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ContactCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
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
                  width: 0.5),
            ),
            child: Icon(icon, color: ColorResources.primaryColor, size: 16),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTextStyles.headingSmall.copyWith(
                  fontSize: 9,
                  color: ColorResources.liteTextColor,
                  letterSpacing: 1.8,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                value,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 15,
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

class _MedicalRow extends StatelessWidget {
  final String label;
  final String value;
  final Color valueColor;
  final bool isItalic;

  const _MedicalRow({
    required this.label,
    required this.value,
    required this.valueColor,
    this.isItalic = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 10,
              color: ColorResources.liteTextColor,
              letterSpacing: 2.0,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: valueColor,
              fontSize: 14,
              fontWeight: FontWeight.w400,
              fontStyle: isItalic ? FontStyle.italic : FontStyle.normal,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}