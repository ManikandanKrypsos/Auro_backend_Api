import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../theme/color/color.dart';
import '../../../../../widgets/app_drop_down.dart';
import '../../cubit/add_patient_cubit.dart';
// ── Static options ─────────────────────────────────────────
const _genders = ['Female', 'Male', 'Other'];
const _skinTypes = ['Normal', 'Dry', 'Oily', 'Combination', 'Sensitive'];
const _marketingSources = [
  {'label': 'Instagram', 'icon': Icons.photo_camera_outlined},
  {'label': 'Website',   'icon': Icons.language_outlined},
  {'label': 'Walk-in',   'icon': Icons.directions_walk_outlined},
  {'label': 'Referral',  'icon': Icons.people_outline},
];

class SectionHeader extends StatelessWidget {
  final IconData icon;
  final String text;
  const SectionHeader({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Row(
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 16),
          const SizedBox(width: 10),
          Text(
            text,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 14,
              fontWeight: FontWeight.w600,
              letterSpacing: 3.0,
            ),
          ),
        ],
      ),
    );
  }
}

// ── GENDER SELECTOR ────────────────────────────────────────
class GenderSelector extends StatelessWidget {
  const GenderSelector();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AddPatientCubit, AddPatientState>(
      buildWhen: (p, c) => p.gender != c.gender,
      builder: (context, state) {
        return Row(
          children: _genders.map((g) {
            final selected = state.gender == g;
            return Expanded(
              child: GestureDetector(
                onTap: () =>
                    context.read<AddPatientCubit>().selectGender(g),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      Container(
                        width: 18,
                        height: 18,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: selected
                                ? ColorResources.primaryColor
                                : ColorResources.liteTextColor,
                            width: 1.5,
                          ),
                        ),
                        child: selected
                            ? Center(
                                child: Container(
                                  width: 9,
                                  height: 9,
                                  decoration: const BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: ColorResources.primaryColor,
                                  ),
                                ),
                              )
                            : null,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        g,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.5,
                          color: selected
                              ? ColorResources.primaryColor
                              : ColorResources.liteTextColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }).toList(),
        );
      },
    );
  }
}

// ── SKIN TYPE DROPDOWN ─────────────────────────────────────
class SkinTypeDropdown extends StatelessWidget {
  const SkinTypeDropdown();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AddPatientCubit, AddPatientState>(
      buildWhen: (p, c) => p.skinType != c.skinType,
      builder: (context, state) {
        return AppDropdown(
          value: state.skinType.isEmpty ? null : state.skinType,
          items: _skinTypes,
          onChanged: (v) {
            if (v != null)
              context.read<AddPatientCubit>().selectSkinType(v);
          },
        );
      },
    );
  }
}

// ── MARKETING SOURCE SELECTOR ──────────────────────────────
class MarketingSourceSelector extends StatelessWidget {
  const MarketingSourceSelector();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AddPatientCubit, AddPatientState>(
      buildWhen: (p, c) => p.marketingSource != c.marketingSource,
      builder: (context, state) {
        return Wrap(
          spacing: 10,
          runSpacing: 10,
          children: _marketingSources.map((src) {
            final label    = src['label'] as String;
            final icon     = src['icon']  as IconData;
            final selected = state.marketingSource == label;
            return GestureDetector(
              onTap: () => context
                  .read<AddPatientCubit>()
                  .selectMarketingSource(label),
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: selected
                      ? ColorResources.primaryColor.withOpacity(0.12)
                      : ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: selected
                        ? ColorResources.primaryColor
                        : ColorResources.borderColor,
                    width: 0.5,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon,
                        size: 13,
                        color: selected
                            ? ColorResources.primaryColor
                            : ColorResources.liteTextColor),
                    const SizedBox(width: 7),
                    Text(
                      label,
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1.5,
                        color: selected
                            ? ColorResources.primaryColor
                            : ColorResources.liteTextColor,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        );
      },
    );
  }
}