import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/profile_add_widget.dart';
import 'package:aura/app/widgets/app_drop_down.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../theme/color/color.dart';
import '../cubit/add_patient_cubit.dart';

// ── Static options ─────────────────────────────────────────
const _genders = ['Female', 'Male', 'Other'];
const _skinTypes = ['Normal', 'Dry', 'Oily', 'Combination', 'Sensitive'];
const _marketingSources = [
  {'label': 'Instagram', 'icon': Icons.photo_camera_outlined},
  {'label': 'Website',   'icon': Icons.language_outlined},
  {'label': 'Walk-in',   'icon': Icons.directions_walk_outlined},
  {'label': 'Referral',  'icon': Icons.people_outline},
];

// ── Screen ─────────────────────────────────────────────────
class AddPatientScreen extends StatelessWidget {
  final bool isedit;
  const AddPatientScreen({super.key,  this.isedit=false});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AddPatientCubit(),
      child:  _AddPatientBody(isedit: isedit,),
    );
  }
}

// ── Body ───────────────────────────────────────────────────
class _AddPatientBody extends StatefulWidget {
  final bool isedit;
   const _AddPatientBody({required this.isedit});

  @override
  State<_AddPatientBody> createState() => _AddPatientBodyState();
}

class _AddPatientBodyState extends State<_AddPatientBody> {
  final _nameCtrl      = TextEditingController();
  final _emailCtrl     = TextEditingController();
  final _phoneCtrl     = TextEditingController();
  final _cityCtrl      = TextEditingController();
  final _countryCtrl   = TextEditingController();
  final _dobCtrl       = TextEditingController();
  final _bloodTypeCtrl = TextEditingController();
  final _allergiesCtrl = TextEditingController();
  final _contrCtrl     = TextEditingController();

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _cityCtrl.dispose();
    _countryCtrl.dispose();
    _dobCtrl.dispose();
    _bloodTypeCtrl.dispose();
    _allergiesCtrl.dispose();
    _contrCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title:widget. isedit? 'EDIT PATIENT': 'ADD NEW PATIENT'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // ── Avatar ───────────────────────────────────
            const Center(child: ProfileAddWidget()),
            const SizedBox(height: 12),

            // ── CONTACT DETAILS ──────────────────────────
            _SectionHeader(icon: Icons.person_outline, text: 'CONTACT DETAILS'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'FULL NAME'),
                  CustomTextField(
                      controller: _nameCtrl, hint: 'Eleanor Vance'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'EMAIL'),
                  CustomTextField(
                      controller: _emailCtrl,
                      hint: 'e.vance@email.com',
                      keyboardType: TextInputType.emailAddress),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'PHONE'),
                  CustomTextField(
                      controller: _phoneCtrl,
                      hint: '+1 (555) 000-0000',
                      keyboardType: TextInputType.phone),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── ADDRESS ──────────────────────────────────
            _SectionHeader(icon: Icons.location_on_outlined, text: 'ADDRESS'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'CITY'),
                  CustomTextField(
                      controller: _cityCtrl, hint: 'New York'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'COUNTRY'),
                  CustomTextField(
                      controller: _countryCtrl, hint: 'United States'),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── BASIC INFORMATION ─────────────────────────
            _SectionHeader(icon: Icons.info_outline, text: 'BASIC INFORMATION'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'GENDER'),
                  const SizedBox(height: 4),
                  const _GenderSelector(),
                  const SizedBox(height: 20),
                  const CustomLabel(text: 'DATE OF BIRTH'),
                  CustomTextField(
                      controller: _dobCtrl,
                      hint: '24 April 2000',
                      keyboardType: TextInputType.datetime),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── MEDICAL SUMMARY ───────────────────────────
            _SectionHeader(
                icon: Icons.medical_services_outlined,
                text: 'MEDICAL SUMMARY'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'BLOOD TYPE'),
                  CustomTextField(
                      controller: _bloodTypeCtrl, hint: 'O Positive'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'ALLERGIES'),
                  CustomTextField(
                      controller: _allergiesCtrl,
                      hint: 'Penicillin, Latex'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'SKIN TYPE'),
                  const _SkinTypeDropdown(),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'CONTRAINDICATIONS'),
                  CustomTextField(
                      controller: _contrCtrl, hint: 'None'),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── MARKETING SOURCE ──────────────────────────
            _SectionHeader(
                icon: Icons.campaign_outlined,
                text: 'MARKETING SOURCE'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: const _MarketingSourceSelector(),
            ),

            const SizedBox(height: 36),

            // ── Save button ───────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  width: double.infinity,
                  height: 52,
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Center(
                    child: Text(
                      'ADD PATIENT',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: Colors.black,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 3.0,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12),

            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'CANCEL & DISCARD',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.35),
                    fontSize: 11,
                    letterSpacing: 2.0,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── SECTION HEADER ─────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String text;
  const _SectionHeader({required this.icon, required this.text});

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
class _GenderSelector extends StatelessWidget {
  const _GenderSelector();

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
class _SkinTypeDropdown extends StatelessWidget {
  const _SkinTypeDropdown();

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
class _MarketingSourceSelector extends StatelessWidget {
  const _MarketingSourceSelector();

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