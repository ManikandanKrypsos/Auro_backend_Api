// ── SOURCE CHIP ────────────────────────────────────────────
import 'package:flutter/material.dart';

import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class SourceChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;

  const SourceChip({
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

class SectionHeader extends StatelessWidget {
  final String label;
  const SectionHeader({required this.label});

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

class ContactCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const ContactCard({
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

class MedicalRow extends StatelessWidget {
  final String label;
  final String value;
  final Color valueColor;
  final bool isItalic;

  const MedicalRow({
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